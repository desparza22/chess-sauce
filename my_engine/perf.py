import chess
from my_engine import engine

def main(depth:int, fens: str, log: str, linear: bool) -> None:
    with open(fens, 'r') as f:
        for line in f:
            fen = line.strip()
            b = chess.Board(fen)
            res = engine.go(b, depth, linear)
            print(res.positions_explored)