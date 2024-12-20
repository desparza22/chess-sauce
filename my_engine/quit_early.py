import chess
from typing import Tuple
import math
from line_profiler import profile

standard_piece_vals = {chess.PAWN:1, chess.KNIGHT:3, chess.BISHOP:3, 
                       chess.ROOK:5, chess.QUEEN:9, chess.KING:0}

@profile
def safe_sqrt(val: float) -> float:
    if val == 0.:
        return 0.01
    return math.sqrt(val)

@profile
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
    root_eval : float
    root_game_phase : float
    
    def __init__(self, current_eval:float, current_game_phase:float):
        self.root_eval = current_eval
        self.root_game_phase = current_game_phase

    @profile
    def should_quit_early(self, 
                          current_eval:float,
                          to_play:chess.Color) -> bool:
        quitable_mg_eval = 1500
        quitable_eg_eval = 700
        quitable_eval = quitable_mg_eval * self.root_game_phase + \
            quitable_eg_eval * (1. - self.root_game_phase)

        eval_diff = self.root_eval - current_eval
        mult = 1.
        if to_play == chess.BLACK:
            mult = -1.
            
        return eval_diff * mult > quitable_eval