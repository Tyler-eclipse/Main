from board import (
    gen_legal_moves,
    has_insufficient_material,
    initial_state,
    make_move,
    record_position,
    unmake_move,
    is_threefold_repetition,
)
from move import Move


def empty_board():
    return [list("........") for _ in range(8)]


def test_white_underpromotions_generated():
    board = empty_board()
    board[7][4] = "K"
    board[0][4] = "k"
    board[1][0] = "P"
    state = initial_state()

    moves = gen_legal_moves(board, state, "w")
    promos = {mv.promo for mv in moves if mv.fr == (1, 0) and mv.to == (0, 0)}

    assert promos == {"Q", "R", "B", "N"}


def test_halfmove_clock_updates_and_unmake_restores():
    board = empty_board()
    board[7][4] = "K"
    board[0][4] = "k"
    board[6][4] = "P"
    board[4][5] = "p"
    state = initial_state()

    # Non-pawn/non-capture move increments.
    board[7][0] = "R"
    mv = Move((7, 0), (7, 1))
    undo = make_move(board, state, mv)
    assert state["halfmove_clock"] == 1
    unmake_move(board, state, mv, undo)
    assert state["halfmove_clock"] == 0

    # Pawn move resets.
    mv = Move((6, 4), (5, 4))
    make_move(board, state, mv)
    assert state["halfmove_clock"] == 0


def test_threefold_repetition_tracking():
    board = empty_board()
    board[7][4] = "K"
    board[0][4] = "k"
    state = initial_state()

    record_position(board, state, "w")
    record_position(board, state, "w")
    assert not is_threefold_repetition(board, state, "w")
    record_position(board, state, "w")
    assert is_threefold_repetition(board, state, "w")


def test_insufficient_material_cases():
    board = empty_board()
    board[7][4] = "K"
    board[0][4] = "k"
    assert has_insufficient_material(board)

    board[6][2] = "N"
    assert has_insufficient_material(board)

    board[6][2] = "."
    board[6][2] = "B"
    board[1][5] = "b"
    assert has_insufficient_material(board)

    board[6][2] = "N"
    assert not has_insufficient_material(board)
