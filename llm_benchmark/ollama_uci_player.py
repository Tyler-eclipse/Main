import argparse
import os
import random
import re
import subprocess
import sys


def extract_uci(text):
    m = re.search(r"\b([a-h][1-8][a-h][1-8][qrbn]?)\b", text.lower())
    return m.group(1) if m else None


def extract_legal_moves(prompt):
    m = re.search(r"Legal moves:\s*(.+)", prompt)
    if not m:
        return []
    raw = m.group(1)
    candidates = [x.strip().lower() for x in raw.split(",")]
    return [mv for mv in candidates if re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?", mv)]


def run_ollama(model, prompt, timeout_s):
    ollama_cmd = "ollama"
    if os.name == "nt":
        candidate = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe")
        if os.path.exists(candidate):
            ollama_cmd = candidate
    return subprocess.run(
        [ollama_cmd, "run", model],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Read chess prompt from stdin and print one UCI move via Ollama."
    )
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama model name.")
    parser.add_argument("--timeout-s", type=float, default=8.0, help="Timeout for one Ollama call.")
    args = parser.parse_args()

    prompt = sys.stdin.read()
    if not prompt.strip():
        print("No prompt received on stdin.", file=sys.stderr)
        sys.exit(2)
    legal_moves = extract_legal_moves(prompt)
    legal_set = set(legal_moves)

    try:
        strict_prompt = (
            "Choose exactly one legal move from the provided legal-moves list.\n"
            "Output exactly one UCI move token and nothing else.\n\n"
            f"{prompt}"
        )
        completed = run_ollama(args.model, strict_prompt, args.timeout_s)
    except FileNotFoundError:
        print("Could not find 'ollama' command. Install Ollama first.", file=sys.stderr)
        sys.exit(2)
    except subprocess.TimeoutExpired:
        if legal_moves:
            print(random.choice(legal_moves))
            return
        print("Ollama request timed out.", file=sys.stderr)
        sys.exit(1)

    if completed.returncode != 0:
        if legal_moves:
            print(random.choice(legal_moves))
            return
        err = completed.stderr.strip() or f"ollama exited with code {completed.returncode}"
        print(err, file=sys.stderr)
        sys.exit(1)

    move = extract_uci(completed.stdout)
    if move in legal_set:
        print(move)
        return

    # Repair pass with an even tighter instruction.
    if legal_moves:
        try:
            repair_prompt = (
                "Respond with exactly one token from this list and nothing else:\n"
                + ", ".join(legal_moves)
            )
            repaired = run_ollama(args.model, repair_prompt, args.timeout_s)
            if repaired.returncode == 0:
                repaired_move = extract_uci(repaired.stdout)
                if repaired_move in legal_set:
                    print(repaired_move)
                    return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Last resort: always return a legal move for the harness.
        print(random.choice(legal_moves))
        return

    if move is None:
        print("No UCI move found in Ollama output.", file=sys.stderr)
    else:
        print(f"Model returned non-legal move: {move}", file=sys.stderr)
    sys.exit(1)

    print(move)


if __name__ == "__main__":
    main()
