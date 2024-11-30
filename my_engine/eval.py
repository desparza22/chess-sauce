import chess
from typing import Callable
from my_engine import eval_piece_vals

large_difference = 1500

eval_functions : list[Callable[[chess.Board], float]] = [eval_piece_vals.eval_piece_vals]

def eval(b: chess.Board) -> float:
    return sum([eval_f(b) for eval_f in eval_functions])
    
def main(fens: str) -> None:
    print("base,sum_square_diffs,phase")
    with open(fens, 'r') as f:
        for line in f:
            fen = line.strip()
            b = chess.Board(fen)
            base = eval(b)
            phase = eval_piece_vals.game_phase(b)
            sum_square_diffs = 0.
            print(f"{base}, ", end="")
            moves = list(b.legal_moves)
            for move in moves:
                b.push(move)
                moves2 = list(b.legal_moves)
                for move2 in moves2[::9]:
                    b.push(move2)
                    node = eval(b)
                    sum_square_diffs += node * node
                    b.pop()
                b.pop()
            print(f"{sum_square_diffs}, ", end="")
            print(f"{phase}")