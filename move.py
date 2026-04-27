from dataclasses import dataclass


@dataclass(frozen=True)
class Move:
    fr: tuple
    to: tuple
    promo: str = None
    is_castle: bool = False
    is_en_passant: bool = False
