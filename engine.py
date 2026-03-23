from dataclasses import dataclass

import gamestate

@dataclass(frozen=True)
class Move:
    fr: tuple  # (r,c)
    to: tuple  # (r,c)
    promo: str = None  # not used yet


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def color_of(p):
    if p == '.': return None
    return 'w' if p.isupper() else 'b'


def enemy(color):
    return 'b' if color == 'w' else 'w'


def find_king(board, color):
    k = 'K' if color == 'w' else 'k'
    for r in range(8):
        for c in range(8):
            if board[r][c] == k:
                return (r, c)
    return None


def is_square_attacked(board, sq, by_color):
    """Return True if sq (r,c) is attacked by by_color."""
    r, c = sq

    # Pawn attacks
    if by_color == 'w':
        for dc in (-1, 1):
            rr, cc = r + 1, c + dc
            if in_bounds(rr, cc) and board[rr][cc] == 'P':
                return True
    else:
        for dc in (-1, 1):
            rr, cc = r - 1, c + dc
            if in_bounds(rr, cc) and board[rr][cc] == 'p':
                return True

    # Knight attacks
    knight = 'N' if by_color == 'w' else 'n'
    for dr, dc in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
        rr, cc = r + dr, c + dc
        if in_bounds(rr, cc) and board[rr][cc] == knight:
            return True

    # King attacks
    king = 'K' if by_color == 'w' else 'k'
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr == 0 and dc == 0: continue
            rr, cc = r + dr, c + dc
            if in_bounds(rr, cc) and board[rr][cc] == king:
                return True

    # Sliding attacks: bishops/queens (diagonals)
    bishops = {'B','Q'} if by_color == 'w' else {'b','q'}
    for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1)]:
        rr, cc = r + dr, c + dc
        while in_bounds(rr, cc):
            p = board[rr][cc]
            if p != '.':
                if p in bishops:
                    return True
                break
            rr += dr; cc += dc

    # Sliding attacks: rooks/queens (orthogonal)
    rooks = {'R','Q'} if by_color == 'w' else {'r','q'}
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        rr, cc = r + dr, c + dc
        while in_bounds(rr, cc):
            p = board[rr][cc]
            if p != '.':
                if p in rooks:
                    return True
                break
            rr += dr; cc += dc

    return False


def make_move(board, mv: Move):
    """Mutate board; return captured piece for undo."""
    fr_r, fr_c = mv.fr
    to_r, to_c = mv.to
    piece = board[fr_r][fr_c]
    captured = board[to_r][to_c]

    #castling
    if piece in ('K', 'k') and abs(to_c - fr_c) == 2:
        # kingside
        if to_c - fr_c == 2:
            board[to_r][to_c] = piece
            board[fr_r][fr_c] = '.'
            if piece == 'K':  # White
                board[7][5] = board[7][7]
                board[7][7] = '.'
            else:  # Black
                board[0][5] = board[0][7]
                board[0][7] = '.'
            return captured
        # queenside
        elif to_c - fr_c == -2:
            board[to_r][to_c] = piece
            board[fr_r][fr_c] = '.'
            if piece == 'K':  # White
                board[7][3] = board[7][0]
                board[7][0] = '.'
            else:  # Black
                board[0][3] = board[0][0]
                board[0][0] = '.'
            return captured

    board[to_r][to_c] = piece
    board[fr_r][fr_c] = '.'
    return captured


def unmake_move(board, mv: Move, captured):
    fr_r, fr_c = mv.fr
    to_r, to_c = mv.to
    piece = board[to_r][to_c]

    # Undo castling
    if piece in ('K', 'k') and abs(to_c - fr_c) == 2:
        # kingside
        if to_c - fr_c == 2:
            board[fr_r][fr_c] = piece
            board[to_r][to_c] = '.'
            if piece == 'K':  # White
                board[7][7] = board[7][5]
                board[7][5] = '.'
            else:  # Black
                board[0][7] = board[0][5]
                board[0][5] = '.'
            return
        # queenside
        elif to_c - fr_c == -2:
            board[fr_r][fr_c] = piece
            board[to_r][to_c] = '.'
            if piece == 'K':  # White
                board[7][0] = board[7][3]
                board[7][3] = '.'
            else:  # Black
                board[0][0] = board[0][3]
                board[0][3] = '.'
            return


    board[fr_r][fr_c] = piece
    board[to_r][to_c] = captured


def gen_pseudo_legal(board, side):
    moves = []
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p == '.' or color_of(p) != side:
                continue

            if p in ('P','p'):
                dir_ = -1 if p == 'P' else 1
                start_row = 6 if p == 'P' else 1

                # forward 1
                rr = r + dir_
                if in_bounds(rr, c) and board[rr][c] == '.':
                    moves.append(Move((r,c),(rr,c)))
                    # forward 2
                    rr2 = r + 2*dir_
                    if r == start_row and in_bounds(rr2, c) and board[rr2][c] == '.':
                        moves.append(Move((r,c),(rr2,c)))
                for dc in (-1, 1):
                    cc = c + dc
                    rr = r + dir_
                    if in_bounds(rr, cc):
                        target = board[rr][cc]
                        if target != '.' and color_of(target) == enemy(side):
                            moves.append(Move((r,c),(rr,cc)))

            elif p in ('N','n'):
                for dr, dc in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
                    rr, cc = r + dr, c + dc
                    if not in_bounds(rr, cc):
                        continue
                    target = board[rr][cc]
                    if target == '.' or color_of(target) == enemy(side):
                        moves.append(Move((r,c),(rr,cc)))

            elif p in ('B','b','R','r','Q','q'):
                dirs = []
                if p.lower() in ('b','q'):
                    dirs += [(-1,-1), (-1,1), (1,-1), (1,1)]
                if p.lower() in ('r','q'):
                    dirs += [(-1,0), (1,0), (0,-1), (0,1)]
                for dr, dc in dirs:
                    rr, cc = r + dr, c + dc
                    while in_bounds(rr, cc):
                        target = board[rr][cc]
                        if target == '.':
                            moves.append(Move((r,c),(rr,cc)))
                        else:
                            if color_of(target) == enemy(side):
                                moves.append(Move((r,c),(rr,cc)))
                            break
                        rr += dr; cc += dc

            elif p in ('K','k'):
                for dr in (-1,0,1):
                    for dc in (-1,0,1):
                        if dr == 0 and dc == 0:
                            continue
                        rr, cc = r + dr, c + dc
                        if not in_bounds(rr, cc):
                            continue
                        target = board[rr][cc]
                        if target == '.' or color_of(target) == enemy(side):
                            moves.append(Move((r,c),(rr,cc)))
                rights = gamestate.castling_rights
                if side=='w' and r==7 and c==4:
                    if rights['wK'] and board[7][5]=='.' and board[7][6]=='.' and not is_square_attacked(board,(7,4),'b') and not is_square_attacked(board,(7,5),'b') and not is_square_attacked(board,(7,6),'b'):
                        moves.append(Move((7,4),(7,6)))  # kingside
                    if rights['wQ'] and board[7][3]=='.' and board[7][2]=='.' and board[7][1]=='.' and not is_square_attacked(board,(7,4),'b') and not is_square_attacked(board,(7,3),'b') and not is_square_attacked(board,(7,2),'b'):
                        moves.append(Move((7,4),(7,2)))  # queenside
                elif side=='b' and r==0 and c==4:
                    if rights['bK'] and board[0][5]=='.' and board[0][6]=='.' and not is_square_attacked(board,(0,4),'w') and not is_square_attacked(board,(0,5),'w') and not is_square_attacked(board,(0,6),'w'):
                        moves.append(Move((0,4),(0,6)))
                    if rights['bQ'] and board[0][3]=='.' and board[0][2]=='.' and board[0][1]=='.' and not is_square_attacked(board,(0,4),'w') and not is_square_attacked(board,(0,3),'w') and not is_square_attacked(board,(0,2),'w'):
                        moves.append(Move((0,4),(0,2)))
    return moves


def gen_legal_moves(board, side):
    legal = []
    for mv in gen_pseudo_legal(board, side):
        cap = make_move(board, mv)
        ksq = find_king(board, side)
        ok = (ksq is not None) and (not is_square_attacked(board, ksq, enemy(side)))
        unmake_move(board, mv, cap)
        if ok:
            legal.append(mv)
    return legal

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