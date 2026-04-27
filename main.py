import copy
import time

import pygame

from board import (
    color_of,
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
from engine import choose_engine_move
from ui import HEIGHT, MARGIN, WIDTH, draw_board, load_images, pixel_to_square


def game_status(board, state, side_to_move):
    if state["halfmove_clock"] >= 100:
        return "Draw by 50-move rule."
    if is_threefold_repetition(board, state, side_to_move):
        return "Draw by repetition."
    if has_insufficient_material(board):
        return "Draw by insufficient material."

    moves = gen_legal_moves(board, state, side_to_move)
    if moves:
        return None

    ksq = find_king(board, side_to_move)
    if ksq and is_square_attacked(board, ksq, enemy(side_to_move)):
        return "Checkmate! Black wins." if side_to_move == "w" else "Checkmate! White wins."
    return "Stalemate!"


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Basic Chess (Pygame)")
    load_images()

    small = pygame.font.SysFont("consolas", 22)

    board = initial_board()
    state = initial_state()
    side_to_move = "w"
    record_position(board, state, side_to_move)
    history = [(copy.deepcopy(board), copy.deepcopy(state), side_to_move)]
    player_side = "w"
    engine_side = "b"

    selected = None
    legal_targets = set()
    depth = 2
    running = True
    clock = pygame.time.Clock()
    message = ""
    engine_thinking = False
    last_engine_ms = None

    def push_history():
        history.append((copy.deepcopy(board), copy.deepcopy(state), side_to_move))

    def restore_from_history():
        nonlocal board, state, side_to_move, selected, legal_targets, message
        board_snapshot, state_snapshot, side_snapshot = history[-1]
        board = copy.deepcopy(board_snapshot)
        state = copy.deepcopy(state_snapshot)
        side_to_move = side_snapshot
        selected = None
        legal_targets = set()
        message = ""

    def undo_turn():
        # If it's player's turn, undo engine + player moves (full turn).
        # If it's engine's turn, undo only player's last move.
        if len(history) <= 1:
            return
        pops = 2 if side_to_move == player_side else 1
        pops = min(pops, len(history) - 1)
        for _ in range(pops):
            history.pop()
        restore_from_history()

    while running:
        clock.tick(60)

        status_now = game_status(board, state, side_to_move)
        if status_now is not None:
            message = status_now
        else:
            message = ""

        if side_to_move == engine_side and not message:
            engine_thinking = True
            draw_board(screen, board, selected, legal_targets)
            status = f"Turn: {'White' if side_to_move == 'w' else 'Black'} | Depth: {depth} | 1-3 depth | U undo | R reset"
            txt = small.render(status, True, (230, 230, 230))
            screen.blit(txt, (MARGIN, 10))
            thinking = small.render("Engine thinking...", True, (255, 220, 120))
            screen.blit(thinking, (MARGIN, HEIGHT - 28))
            pygame.display.flip()

            start = time.perf_counter()
            mv = choose_engine_move(board, state, engine_side, depth=depth)
            last_engine_ms = (time.perf_counter() - start) * 1000.0
            engine_thinking = False
            if mv is not None:
                make_move(board, state, mv)
                side_to_move = enemy(side_to_move)
                record_position(board, state, side_to_move)
                push_history()
            selected = None
            legal_targets = set()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    board = initial_board()
                    state = initial_state()
                    side_to_move = "w"
                    record_position(board, state, side_to_move)
                    history = [(copy.deepcopy(board), copy.deepcopy(state), side_to_move)]
                    selected = None
                    legal_targets = set()
                    message = ""
                elif event.key == pygame.K_1:
                    depth = 1
                elif event.key == pygame.K_2:
                    depth = 2
                elif event.key == pygame.K_3:
                    depth = 3
                elif event.key == pygame.K_u:
                    undo_turn()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if side_to_move != player_side or message:
                    continue

                sq = pixel_to_square(pygame.mouse.get_pos())
                if sq is None:
                    continue

                r, c = sq
                p = board[r][c]

                if selected is None:
                    if p != "." and color_of(p) == player_side:
                        selected = sq
                        moves = gen_legal_moves(board, state, player_side)
                        legal_targets = {mv.to for mv in moves if mv.fr == selected}
                else:
                    moves = gen_legal_moves(board, state, player_side)
                    chosen = None
                    for mv in moves:
                        if mv.fr == selected and mv.to == sq:
                            chosen = mv
                            break

                    if chosen is not None:
                        make_move(board, state, chosen)
                        side_to_move = enemy(side_to_move)
                        record_position(board, state, side_to_move)
                        push_history()

                    selected = None
                    legal_targets = set()

        draw_board(screen, board, selected, legal_targets)

        status = f"Turn: {'White' if side_to_move == 'w' else 'Black'} | Depth: {depth} | 1-3 depth | U undo | R reset"
        txt = small.render(status, True, (230, 230, 230))
        screen.blit(txt, (MARGIN, 10))

        if message:
            msg = small.render(message, True, (255, 200, 200))
            screen.blit(msg, (MARGIN, HEIGHT - 28))
        elif engine_thinking:
            msg = small.render("Engine thinking...", True, (255, 220, 120))
            screen.blit(msg, (MARGIN, HEIGHT - 28))
        elif last_engine_ms is not None:
            msg = small.render(f"Engine move time: {last_engine_ms:.0f} ms", True, (200, 220, 255))
            screen.blit(msg, (MARGIN, HEIGHT - 28))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
