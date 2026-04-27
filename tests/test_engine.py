from board import initial_state
from engine import MATE_SCORE, alphabeta


def empty_board():
    return [list("........") for _ in range(8)]


def test_checkmate_score_includes_depth():
    board = empty_board()
    # Black to move is checkmated.
    board[0][0] = "k"
    board[1][1] = "Q"
    board[2][2] = "K"

    state = initial_state()
    score = alphabeta(board, state, "b", depth=2, alpha=-10**9, beta=10**9)
    assert score == MATE_SCORE + 2


def test_draw_by_fifty_move_rule_in_search():
    board = empty_board()
    board[7][4] = "K"
    board[0][4] = "k"

    state = initial_state()
    state["halfmove_clock"] = 100

    score = alphabeta(board, state, "w", depth=3, alpha=-10**9, beta=10**9)
    assert score == 0
