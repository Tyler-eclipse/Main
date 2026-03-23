from constants import PIECE_VALUES
from engine import Move
from engine import gen_legal_moves, make_move, unmake_move, find_king, is_square_attacked, enemy

def evaluate(board):
    s = 0
    for r in range(8):
        for c in range(8):
            s += PIECE_VALUES[board[r][c]]
    return s  # positive = good for White


def alphabeta(board, side, depth, alpha, beta):
    # Terminal / leaf
    moves = gen_legal_moves(board, side)
    if depth == 0 or not moves:
        # simple checkmate/stalemate handling
        ksq = find_king(board, side)
        if not moves and ksq and is_square_attacked(board, ksq, enemy(side)):
            # side to move is checkmated
            return -99999 if side == 'w' else 99999
        return evaluate(board)

    if side == 'w':
        best = -10**9
        for mv in moves:
            cap = make_move(board, mv)
            val = alphabeta(board, 'b', depth-1, alpha, beta)
            unmake_move(board, mv, cap)
            best = max(best, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best
    else:
        best = 10**9
        for mv in moves:
            cap = make_move(board, mv)
            val = alphabeta(board, 'w', depth-1, alpha, beta)
            unmake_move(board, mv, cap)
            best = min(best, val)
            beta = min(beta, val)
            if beta <= alpha:
                break
        return best


def choose_engine_move(board, side, depth=2):
    moves = gen_legal_moves(board, side)
    if not moves:
        return None
    best_mv = None
    if side == 'w':
        best_val = -10**9
        for mv in moves:
            cap = make_move(board, mv)
            val = alphabeta(board, 'b', depth-1, -10**9, 10**9)
            unmake_move(board, mv, cap)
            if val > best_val:
                best_val = val
                best_mv = mv
    else:
        best_val = 10**9
        for mv in moves:
            cap = make_move(board, mv)
            val = alphabeta(board, 'w', depth-1, -10**9, 10**9)
            unmake_move(board, mv, cap)
            if val < best_val:
                best_val = val
                best_mv = mv
    return best_mv