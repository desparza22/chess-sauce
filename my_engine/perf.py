import chess
from my_engine import engine

def main(depth:int, fens: str, linear: bool) -> None:
    with open(fens, 'r') as f:
        for line in f:
            fen = line.strip()
            b = chess.Board(fen)
            res, stats = engine.go(b, depth, linear)
            print(f"fen: {fen}")
            print(f"initial_eval: {stats.initial_eval:.3f} final_eval: {engine.float_of_eval(res.sorted_moves)}")
            print(f"best move: {engine.best_move_of_eval(res.sorted_moves)}")