from move import Move


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def color_of(p):
    if p == ".":
        return None
    return "w" if p.isupper() else "b"


def enemy(color):
    return "b" if color == "w" else "w"


def find_king(board, color):
    k = "K" if color == "w" else "k"
    for r in range(8):
        for c in range(8):
            if board[r][c] == k:
                return (r, c)
    return None


def initial_board():
    return [
        list("rnbqkbnr"),
        list("pppppppp"),
        list("........"),
        list("........"),
        list("........"),
        list("........"),
        list("PPPPPPPP"),
        list("RNBQKBNR"),
    ]


def initial_state():
    return {
        "ep": None,
        "castle": {
            "wK": True,
            "wQ": True,
            "bK": True,
            "bQ": True,
        },
        "halfmove_clock": 0,
        "position_counts": {},
    }


def is_square_attacked(board, sq, by_color):
    r, c = sq

    if by_color == "w":
        for dc in (-1, 1):
            rr, cc = r + 1, c + dc
            if in_bounds(rr, cc) and board[rr][cc] == "P":
                return True
    else:
        for dc in (-1, 1):
            rr, cc = r - 1, c + dc
            if in_bounds(rr, cc) and board[rr][cc] == "p":
                return True

    knight = "N" if by_color == "w" else "n"
    for dr, dc in [
        (-2, -1),
        (-2, 1),
        (-1, -2),
        (-1, 2),
        (1, -2),
        (1, 2),
        (2, -1),
        (2, 1),
    ]:
        rr, cc = r + dr, c + dc
        if in_bounds(rr, cc) and board[rr][cc] == knight:
            return True

    king = "K" if by_color == "w" else "k"
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if in_bounds(rr, cc) and board[rr][cc] == king:
                return True

    bishops = {"B", "Q"} if by_color == "w" else {"b", "q"}
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        rr, cc = r + dr, c + dc
        while in_bounds(rr, cc):
            p = board[rr][cc]
            if p != ".":
                if p in bishops:
                    return True
                break
            rr += dr
            cc += dc

    rooks = {"R", "Q"} if by_color == "w" else {"r", "q"}
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        rr, cc = r + dr, c + dc
        while in_bounds(rr, cc):
            p = board[rr][cc]
            if p != ".":
                if p in rooks:
                    return True
                break
            rr += dr
            cc += dc

    return False


def make_move(board, state, mv: Move):
    fr_r, fr_c = mv.fr
    to_r, to_c = mv.to
    piece = board[fr_r][fr_c]

    undo = {
        "captured": board[to_r][to_c],
        "prev_ep": state["ep"],
        "prev_castle": state["castle"].copy(),
        "prev_halfmove": state["halfmove_clock"],
        "rook_move": None,
        "ep_captured_square": None,
    }

    state["ep"] = None

    if mv.is_en_passant:
        cap_r = fr_r
        cap_c = to_c
        undo["captured"] = board[cap_r][cap_c]
        undo["ep_captured_square"] = (cap_r, cap_c)
        board[cap_r][cap_c] = "."

    board[to_r][to_c] = piece
    board[fr_r][fr_c] = "."

    if piece.lower() == "p" or undo["captured"] != ".":
        state["halfmove_clock"] = 0
    else:
        state["halfmove_clock"] += 1

    if mv.is_castle:
        if piece == "K":
            if to_c == 6:
                board[7][5] = board[7][7]
                board[7][7] = "."
                undo["rook_move"] = ((7, 7), (7, 5))
            else:
                board[7][3] = board[7][0]
                board[7][0] = "."
                undo["rook_move"] = ((7, 0), (7, 3))
        elif piece == "k":
            if to_c == 6:
                board[0][5] = board[0][7]
                board[0][7] = "."
                undo["rook_move"] = ((0, 7), (0, 5))
            else:
                board[0][3] = board[0][0]
                board[0][0] = "."
                undo["rook_move"] = ((0, 0), (0, 3))

    if piece == "P" and fr_r == 6 and to_r == 4:
        state["ep"] = (5, fr_c)
    elif piece == "p" and fr_r == 1 and to_r == 3:
        state["ep"] = (2, fr_c)

    if piece == "K":
        state["castle"]["wK"] = False
        state["castle"]["wQ"] = False
    elif piece == "k":
        state["castle"]["bK"] = False
        state["castle"]["bQ"] = False

    if piece == "R":
        if (fr_r, fr_c) == (7, 0):
            state["castle"]["wQ"] = False
        elif (fr_r, fr_c) == (7, 7):
            state["castle"]["wK"] = False
    elif piece == "r":
        if (fr_r, fr_c) == (0, 0):
            state["castle"]["bQ"] = False
        elif (fr_r, fr_c) == (0, 7):
            state["castle"]["bK"] = False

    captured_square = (to_r, to_c)
    if mv.is_en_passant:
        captured_square = undo["ep_captured_square"]

    captured_piece = undo["captured"]
    if captured_piece == "R":
        if captured_square == (7, 0):
            state["castle"]["wQ"] = False
        elif captured_square == (7, 7):
            state["castle"]["wK"] = False
    elif captured_piece == "r":
        if captured_square == (0, 0):
            state["castle"]["bQ"] = False
        elif captured_square == (0, 7):
            state["castle"]["bK"] = False

    if mv.promo is not None:
        board[to_r][to_c] = mv.promo

    return undo


def unmake_move(board, state, mv: Move, undo):
    fr_r, fr_c = mv.fr
    to_r, to_c = mv.to

    state["ep"] = undo["prev_ep"]
    state["castle"] = undo["prev_castle"].copy()
    state["halfmove_clock"] = undo["prev_halfmove"]

    moved_piece = board[to_r][to_c]
    original_piece = board[to_r][to_c]

    if mv.promo is not None:
        original_piece = "P" if moved_piece.isupper() else "p"

    board[fr_r][fr_c] = original_piece

    if mv.is_en_passant:
        board[to_r][to_c] = "."
        cap_r, cap_c = undo["ep_captured_square"]
        board[cap_r][cap_c] = undo["captured"]
    else:
        board[to_r][to_c] = undo["captured"]

    if undo["rook_move"] is not None:
        rook_from, rook_to = undo["rook_move"]
        rf_r, rf_c = rook_from
        rt_r, rt_c = rook_to
        board[rf_r][rf_c] = board[rt_r][rt_c]
        board[rt_r][rt_c] = "."


def gen_pseudo_legal(board, state, side):
    moves = []

    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p == "." or color_of(p) != side:
                continue

            if p in ("P", "p"):
                dir_ = -1 if p == "P" else 1
                start_row = 6 if p == "P" else 1
                promotion_row = 0 if p == "P" else 7
                promo_pieces = ("Q", "R", "B", "N") if p == "P" else ("q", "r", "b", "n")

                rr = r + dir_
                if in_bounds(rr, c) and board[rr][c] == ".":
                    if rr == promotion_row:
                        for promo_piece in promo_pieces:
                            moves.append(Move((r, c), (rr, c), promo=promo_piece))
                    else:
                        moves.append(Move((r, c), (rr, c)))

                    rr2 = r + 2 * dir_
                    if r == start_row and in_bounds(rr2, c) and board[rr2][c] == ".":
                        moves.append(Move((r, c), (rr2, c)))

                for dc in (-1, 1):
                    cc = c + dc
                    rr = r + dir_
                    if not in_bounds(rr, cc):
                        continue

                    target = board[rr][cc]
                    if target != "." and color_of(target) == enemy(side) and target.lower() != "k":
                        if rr == promotion_row:
                            for promo_piece in promo_pieces:
                                moves.append(Move((r, c), (rr, cc), promo=promo_piece))
                        else:
                            moves.append(Move((r, c), (rr, cc)))

                    if state["ep"] == (rr, cc):
                        adj = board[r][cc]
                        if adj != "." and color_of(adj) == enemy(side) and adj.lower() == "p":
                            moves.append(Move((r, c), (rr, cc), is_en_passant=True))

            elif p in ("N", "n"):
                for dr, dc in [
                    (-2, -1),
                    (-2, 1),
                    (-1, -2),
                    (-1, 2),
                    (1, -2),
                    (1, 2),
                    (2, -1),
                    (2, 1),
                ]:
                    rr, cc = r + dr, c + dc
                    if not in_bounds(rr, cc):
                        continue
                    target = board[rr][cc]
                    if target == "." or (color_of(target) == enemy(side) and target.lower() != "k"):
                        moves.append(Move((r, c), (rr, cc)))

            elif p in ("B", "b", "R", "r", "Q", "q"):
                dirs = []
                if p.lower() in ("b", "q"):
                    dirs += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                if p.lower() in ("r", "q"):
                    dirs += [(-1, 0), (1, 0), (0, -1), (0, 1)]

                for dr, dc in dirs:
                    rr, cc = r + dr, c + dc
                    while in_bounds(rr, cc):
                        target = board[rr][cc]
                        if target == ".":
                            moves.append(Move((r, c), (rr, cc)))
                        else:
                            if color_of(target) == enemy(side) and target.lower() != "k":
                                moves.append(Move((r, c), (rr, cc)))
                            break
                        rr += dr
                        cc += dc

            elif p in ("K", "k"):
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        rr, cc = r + dr, c + dc
                        if not in_bounds(rr, cc):
                            continue
                        target = board[rr][cc]
                        if target == "." or (color_of(target) == enemy(side) and target.lower() != "k"):
                            moves.append(Move((r, c), (rr, cc)))

                if side == "w" and (r, c) == (7, 4):
                    if state["castle"]["wK"]:
                        if board[7][5] == "." and board[7][6] == "." and board[7][7] == "R":
                            if (
                                not is_square_attacked(board, (7, 4), "b")
                                and not is_square_attacked(board, (7, 5), "b")
                                and not is_square_attacked(board, (7, 6), "b")
                            ):
                                moves.append(Move((7, 4), (7, 6), is_castle=True))
                    if state["castle"]["wQ"]:
                        if (
                            board[7][1] == "."
                            and board[7][2] == "."
                            and board[7][3] == "."
                            and board[7][0] == "R"
                        ):
                            if (
                                not is_square_attacked(board, (7, 4), "b")
                                and not is_square_attacked(board, (7, 3), "b")
                                and not is_square_attacked(board, (7, 2), "b")
                            ):
                                moves.append(Move((7, 4), (7, 2), is_castle=True))

                elif side == "b" and (r, c) == (0, 4):
                    if state["castle"]["bK"]:
                        if board[0][5] == "." and board[0][6] == "." and board[0][7] == "r":
                            if (
                                not is_square_attacked(board, (0, 4), "w")
                                and not is_square_attacked(board, (0, 5), "w")
                                and not is_square_attacked(board, (0, 6), "w")
                            ):
                                moves.append(Move((0, 4), (0, 6), is_castle=True))
                    if state["castle"]["bQ"]:
                        if (
                            board[0][1] == "."
                            and board[0][2] == "."
                            and board[0][3] == "."
                            and board[0][0] == "r"
                        ):
                            if (
                                not is_square_attacked(board, (0, 4), "w")
                                and not is_square_attacked(board, (0, 3), "w")
                                and not is_square_attacked(board, (0, 2), "w")
                            ):
                                moves.append(Move((0, 4), (0, 2), is_castle=True))

    return moves


def gen_legal_moves(board, state, side):
    legal = []
    for mv in gen_pseudo_legal(board, state, side):
        undo = make_move(board, state, mv)
        ksq = find_king(board, side)
        ok = (ksq is not None) and (not is_square_attacked(board, ksq, enemy(side)))
        unmake_move(board, state, mv, undo)
        if ok:
            legal.append(mv)
    return legal


def position_key(board, state, side_to_move):
    board_part = "".join("".join(row) for row in board)
    castle = state["castle"]
    castle_part = (
        ("K" if castle["wK"] else "")
        + ("Q" if castle["wQ"] else "")
        + ("k" if castle["bK"] else "")
        + ("q" if castle["bQ"] else "")
    ) or "-"
    ep = state["ep"]
    ep_part = "-" if ep is None else f"{ep[0]}{ep[1]}"
    return f"{board_part}|{side_to_move}|{castle_part}|{ep_part}"


def record_position(board, state, side_to_move):
    key = position_key(board, state, side_to_move)
    counts = state["position_counts"]
    counts[key] = counts.get(key, 0) + 1
    return key


def unrecord_position(state, key):
    counts = state["position_counts"]
    if key not in counts:
        return
    if counts[key] <= 1:
        del counts[key]
    else:
        counts[key] -= 1


def is_threefold_repetition(board, state, side_to_move):
    key = position_key(board, state, side_to_move)
    return state["position_counts"].get(key, 0) >= 3


def has_insufficient_material(board):
    white_minors = []
    black_minors = []

    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p in (".", "K", "k"):
                continue
            if p in ("P", "p", "R", "r", "Q", "q"):
                return False
            if p == "N":
                white_minors.append(("N", None))
            elif p == "n":
                black_minors.append(("n", None))
            elif p == "B":
                white_minors.append(("B", (r + c) % 2))
            elif p == "b":
                black_minors.append(("b", (r + c) % 2))

    total_white = len(white_minors)
    total_black = len(black_minors)

    if total_white == 0 and total_black == 0:
        return True
    if total_white == 1 and total_black == 0:
        return True
    if total_white == 0 and total_black == 1:
        return True

    # K+B vs K+B with bishops on same color squares.
    if total_white == 1 and total_black == 1:
        w_piece, w_color = white_minors[0]
        b_piece, b_color = black_minors[0]
        if w_piece == "B" and b_piece == "b" and w_color == b_color:
            return True

    return False
