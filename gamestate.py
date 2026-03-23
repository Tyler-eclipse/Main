from engine import initial_board


class GameState:
    def __init__(self):
        self.board = initial_board()
        self.side_to_move = 'w'
        self.castling_rights = {
            'wK': True, 'wQ': True, 'bK': True, 'bQ': True
        }
        self.en_passant_target = None
        