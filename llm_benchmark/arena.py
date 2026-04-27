import argparse
import pathlib
import random
import re
import subprocess
import sys
import time


# Allow running as: python llm_benchmark/arena.py
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from board import (  # noqa: E402
    enemy,
    find_king,
    gen_legal_moves,
    has_insufficient_material,
    initial_board,
    initial_state,
    is_square_attacked,
    is_threefold_repetition,
    make_move,
    record_position,
)
from engine import choose_engine_move  # noqa: E402


FILES = "abcdefgh"


def rc_to_alg(rc):
    r, c = rc
    return f"{FILES[c]}{8 - r}"


def move_to_uci(mv):
    base = f"{rc_to_alg(mv.fr)}{rc_to_alg(mv.to)}"
    if mv.promo:
        return base + mv.promo.lower()
    return base


def parse_uci_token(text):
    m = re.search(r"\b([a-h][1-8][a-h][1-8][qrbn]?)\b", text.lower())
    return m.group(1) if m else None


def board_to_text(board):
    rows = []
    for r in range(8):
        rows.append(" ".join(board[r]))
    return "\n".join(rows)


def game_status(board, state, side_to_move):
    if state["halfmove_clock"] >= 100:
        return "draw_50_move"
    if is_threefold_repetition(board, state, side_to_move):
        return "draw_repetition"
    if has_insufficient_material(board):
        return "draw_insufficient_material"

    moves = gen_legal_moves(board, state, side_to_move)
    if moves:
        return None

    ksq = find_king(board, side_to_move)
    if ksq and is_square_attacked(board, ksq, enemy(side_to_move)):
        return "checkmate_black_wins" if side_to_move == "w" else "checkmate_white_wins"
    return "stalemate"


def ask_external_llm(command, prompt, timeout_s):
    try:
        completed = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            shell=True,
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        if stderr:
            return None, f"nonzero_exit:{completed.returncode}:{stderr}"
        return None, f"nonzero_exit:{completed.returncode}"

    token = parse_uci_token(completed.stdout)
    return token, None


def choose_llm_move(board, state, side, llm_command, timeout_s, retries, rng):
    legal_moves = gen_legal_moves(board, state, side)
    if not legal_moves:
        return None, {"invalid_attempts": 0, "fallback_used": False, "error": None}

    legal_by_uci = {move_to_uci(mv): mv for mv in legal_moves}
    legal_list = sorted(legal_by_uci.keys())
    board_txt = board_to_text(board)

    invalid_attempts = 0
    error = None
    for _ in range(retries + 1):
        prompt = (
            "You are playing chess.\n"
            f"Side to move: {'white' if side == 'w' else 'black'}\n"
            "Return exactly one legal move in UCI format and nothing else.\n"
            f"Legal moves: {', '.join(legal_list)}\n"
            "Board (8th rank to 1st rank; uppercase=White, lowercase=Black):\n"
            f"{board_txt}\n"
        )

        token, err = ask_external_llm(llm_command, prompt, timeout_s)
        if err is not None:
            if "Could not find 'ollama' command" in err or "not recognized as a name of a cmdlet" in err:
                raise RuntimeError(
                    "LLM command failed because Ollama is not installed or not in PATH. "
                    "Install Ollama and verify 'ollama --version' works."
                )
            error = err
            invalid_attempts += 1
            continue
        if token in legal_by_uci:
            return legal_by_uci[token], {
                "invalid_attempts": invalid_attempts,
                "fallback_used": False,
                "error": None,
            }
        invalid_attempts += 1

    fallback = rng.choice(legal_moves)
    return fallback, {"invalid_attempts": invalid_attempts, "fallback_used": True, "error": error}


def play_one_game(game_idx, engine_depth, max_plies, llm_command, llm_timeout_s, retries, rng):
    board = initial_board()
    state = initial_state()
    side_to_move = "w"
    record_position(board, state, side_to_move)

    engine_side = "w" if game_idx % 2 == 0 else "b"
    llm_side = enemy(engine_side)

    stats = {
        "plies": 0,
        "engine_side": engine_side,
        "llm_side": llm_side,
        "llm_invalid_attempts": 0,
        "llm_fallback_moves": 0,
        "engine_think_ms": 0.0,
        "llm_think_ms": 0.0,
    }

    while stats["plies"] < max_plies:
        status = game_status(board, state, side_to_move)
        if status is not None:
            return status, stats

        if side_to_move == engine_side:
            t0 = time.perf_counter()
            mv = choose_engine_move(board, state, side_to_move, depth=engine_depth)
            stats["engine_think_ms"] += (time.perf_counter() - t0) * 1000.0
        else:
            t0 = time.perf_counter()
            mv, llm_meta = choose_llm_move(
                board,
                state,
                side_to_move,
                llm_command=llm_command,
                timeout_s=llm_timeout_s,
                retries=retries,
                rng=rng,
            )
            stats["llm_think_ms"] += (time.perf_counter() - t0) * 1000.0
            stats["llm_invalid_attempts"] += llm_meta["invalid_attempts"]
            if llm_meta["fallback_used"]:
                stats["llm_fallback_moves"] += 1

        if mv is None:
            # Defensive fallback; normally handled by status checks.
            return "no_legal_move", stats

        make_move(board, state, mv)
        side_to_move = enemy(side_to_move)
        record_position(board, state, side_to_move)
        stats["plies"] += 1

    return "draw_max_plies", stats


def engine_result_from_status(status, engine_side):
    if status.startswith("draw") or status == "stalemate":
        return "D"
    if status == "checkmate_white_wins":
        return "W" if engine_side == "w" else "L"
    if status == "checkmate_black_wins":
        return "W" if engine_side == "b" else "L"
    return "D"


def main():
    parser = argparse.ArgumentParser(description="Compare alpha-beta engine vs external LLM player.")
    parser.add_argument("--games", type=int, default=10, help="Number of games to run (colors alternate).")
    parser.add_argument("--engine-depth", type=int, default=2, help="Alpha-beta depth for the engine.")
    parser.add_argument("--max-plies", type=int, default=200, help="Safety cap for game length.")
    parser.add_argument(
        "--llm-command",
        type=str,
        required=True,
        help="Shell command that reads prompt from stdin and prints one UCI move.",
    )
    parser.add_argument("--llm-timeout-s", type=float, default=20.0, help="Timeout per LLM move.")
    parser.add_argument("--llm-retries", type=int, default=1, help="Retries after invalid LLM responses.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic fallback moves.")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    total_w = 0
    total_d = 0
    total_l = 0
    total_plies = 0
    total_engine_ms = 0.0
    total_llm_ms = 0.0
    total_invalid = 0
    total_fallbacks = 0

    print("Running benchmark...")
    print(f"games={args.games}, engine_depth={args.engine_depth}, max_plies={args.max_plies}")

    for i in range(args.games):
        status, st = play_one_game(
            game_idx=i,
            engine_depth=args.engine_depth,
            max_plies=args.max_plies,
            llm_command=args.llm_command,
            llm_timeout_s=args.llm_timeout_s,
            retries=args.llm_retries,
            rng=rng,
        )
        res = engine_result_from_status(status, st["engine_side"])
        if res == "W":
            total_w += 1
        elif res == "D":
            total_d += 1
        else:
            total_l += 1

        total_plies += st["plies"]
        total_engine_ms += st["engine_think_ms"]
        total_llm_ms += st["llm_think_ms"]
        total_invalid += st["llm_invalid_attempts"]
        total_fallbacks += st["llm_fallback_moves"]

        print(
            f"Game {i+1}/{args.games}: status={status}, "
            f"engine_side={st['engine_side']}, result={res}, plies={st['plies']}"
        )

    avg_plies = total_plies / max(1, args.games)
    avg_engine_ms = total_engine_ms / max(1, total_plies // 2)
    avg_llm_ms = total_llm_ms / max(1, total_plies // 2)

    print("\n=== Summary (Engine perspective) ===")
    print(f"W-D-L: {total_w}-{total_d}-{total_l}")
    print(f"Average plies per game: {avg_plies:.1f}")
    print(f"Approx avg engine think time per move: {avg_engine_ms:.1f} ms")
    print(f"Approx avg LLM think time per move: {avg_llm_ms:.1f} ms")
    print(f"LLM invalid attempts: {total_invalid}")
    print(f"LLM fallback moves used: {total_fallbacks}")


if __name__ == "__main__":
    main()
