import os

import pygame

SQUARE = 80
MARGIN = 40
WIDTH = MARGIN * 2 + SQUARE * 8
HEIGHT = MARGIN * 2 + SQUARE * 8

PIECE_IMAGES = {}


def load_images():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mapping = {
        "P": "white-pawn.png",
        "N": "white-knight.png",
        "B": "white-bishop.png",
        "R": "white-rook.png",
        "Q": "white-queen.png",
        "K": "white-king.png",
        "p": "black-pawn.png",
        "n": "black-knight.png",
        "b": "black-bishop.png",
        "r": "black-rook.png",
        "q": "black-queen.png",
        "k": "black-king.png",
    }

    candidate_dirs = [
        os.path.join(base_dir, "pieces-basic-png"),
        base_dir,
    ]

    for piece, filename in mapping.items():
        path = None
        for candidate_dir in candidate_dirs:
            candidate_path = os.path.join(candidate_dir, filename)
            if os.path.exists(candidate_path):
                path = candidate_path
                break
        if path is None:
            raise FileNotFoundError(
                f"Could not find image '{filename}'. "
                f"Tried: {', '.join(candidate_dirs)}"
            )
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, (SQUARE, SQUARE))
        PIECE_IMAGES[piece] = img


def draw_board(screen, board, selected=None, legal_targets=None):
    screen.fill((30, 30, 30))

    for r in range(8):
        for c in range(8):
            x = MARGIN + c * SQUARE
            y = MARGIN + r * SQUARE
            light = (r + c) % 2 == 0
            color = (235, 235, 208) if light else (119, 148, 85)
            pygame.draw.rect(screen, color, (x, y, SQUARE, SQUARE))

            if selected == (r, c):
                pygame.draw.rect(screen, (255, 215, 0), (x, y, SQUARE, SQUARE), 4)

            if legal_targets and (r, c) in legal_targets:
                pygame.draw.circle(screen, (20, 20, 20), (x + SQUARE // 2, y + SQUARE // 2), 10)

            p = board[r][c]
            if p != ".":
                screen.blit(PIECE_IMAGES[p], (x, y))

    pygame.draw.rect(screen, (220, 220, 220), (MARGIN, MARGIN, 8 * SQUARE, 8 * SQUARE), 2)


def pixel_to_square(pos):
    x, y = pos
    x -= MARGIN
    y -= MARGIN
    if x < 0 or y < 0:
        return None
    c = x // SQUARE
    r = y // SQUARE
    if 0 <= r < 8 and 0 <= c < 8:
        return (int(r), int(c))
    return None
