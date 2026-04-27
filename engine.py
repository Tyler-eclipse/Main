import random

from board import (
    enemy,
    find_king,
    gen_legal_moves,
    has_insufficient_material,
    is_square_attacked,
    is_threefold_repetition,
    make_move,
    record_position,
    unmake_move,
    unrecord_position,
)
from constants import PIECE_VALUES

MATE_SCORE = 100000


def order_moves(board, moves):
    return sorted(
        moves,
        key=lambda mv: abs(PIECE_VALUES[board[mv.to[0]][mv.to[1]]]),
        reverse=True,
    )


def evaluate(board, state):
    score = 0

    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p == ".":
                continue

            score += PIECE_VALUES[p]

            if 2 <= r <= 5 and 2 <= c <= 5:
                score += 15 if p.isupper() else -15

            if p == "N" and r < 7:
                score += 15
            if p == "B" and r < 7:
                score += 15
            if p == "n" and r > 0:
                score -= 15
            if p == "b" and r > 0:
                score -= 15

    return score


def alphabeta(board, state, side, depth, alpha, beta):
    if depth == 0:
        return evaluate(board, state)

    if state["halfmove_clock"] >= 100:
        return 0
    if has_insufficient_material(board):
        return 0
    if is_threefold_repetition(board, state, side):
        return 0

    moves = order_moves(board, gen_legal_moves(board, state, side))

    if not moves:
        ksq = find_king(board, side)
        if not moves and ksq and is_square_attacked(board, ksq, enemy(side)):
            return (-MATE_SCORE - depth) if side == "w" else (MATE_SCORE + depth)
        if not moves:
            return 0

    if side == "w":
        best = -10**9
        for mv in moves:
            undo = make_move(board, state, mv)
            next_side = enemy(side)
            key = record_position(board, state, next_side)
            val = alphabeta(board, state, "b", depth - 1, alpha, beta)
            unrecord_position(state, key)
            unmake_move(board, state, mv, undo)
            best = max(best, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best

    best = 10**9
    for mv in moves:
        undo = make_move(board, state, mv)
        next_side = enemy(side)
        key = record_position(board, state, next_side)
        val = alphabeta(board, state, "w", depth - 1, alpha, beta)
        unrecord_position(state, key)
        unmake_move(board, state, mv, undo)
        best = min(best, val)
        beta = min(beta, val)
        if beta <= alpha:
            break
    return best


def choose_engine_move(board, state, side, depth=3):
    moves = order_moves(board, gen_legal_moves(board, state, side))
    if not moves:
        return None

    best_moves = []

    if side == "w":
        best_val = -10**9
        for mv in moves:
            undo = make_move(board, state, mv)
            key = record_position(board, state, "b")
            val = alphabeta(board, state, "b", depth - 1, -10**9, 10**9)
            unrecord_position(state, key)
            unmake_move(board, state, mv, undo)

            if val > best_val:
                best_val = val
                best_moves = [mv]
            elif val == best_val:
                best_moves.append(mv)
    else:
        best_val = 10**9
        for mv in moves:
            undo = make_move(board, state, mv)
            key = record_position(board, state, "w")
            val = alphabeta(board, state, "w", depth - 1, -10**9, 10**9)
            unrecord_position(state, key)
            unmake_move(board, state, mv, undo)

            if val < best_val:
                best_val = val
                best_moves = [mv]
            elif val == best_val:
                best_moves.append(mv)

    return random.choice(best_moves)