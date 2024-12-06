import chess
from typing import Tuple
import math

standard_piece_vals = {chess.PAWN:1, chess.KNIGHT:3, chess.BISHOP:3, 
                       chess.ROOK:5, chess.QUEEN:9, chess.KING:0}

def safe_sqrt(val: float) -> float:
    if val == 0.:
        return 0.01
    return math.sqrt(val)

def board_ratios(b:chess.Board) -> Tuple[float, float]:
    white_sum = 0.
    black_sum = 0.
    for _, piece in b.piece_map().items():
        val = standard_piece_vals[piece.piece_type]
        if piece.color == chess.WHITE:
            white_sum += val
        else:
            black_sum += val
    return (black_sum - white_sum) / safe_sqrt(black_sum), \
        (white_sum - black_sum) / safe_sqrt(white_sum)

        

class QuitEarly:
    root_ratio_white: float
    root_ratio_black: float
    
    def __init__(self, b:chess.Board):
        self.root_ratio_white, self.root_ratio_black = board_ratios(b)


    def should_quit_early(self, b:chess.Board) -> bool:
        current_white, current_black = board_ratios(b)
        if b.turn == chess.WHITE:
            root_ratio = self.root_ratio_white
            current_ratio = current_white
        else:
            root_ratio = self.root_ratio_black
            current_ratio = current_black
         
        res = current_ratio - root_ratio > 1
        return res