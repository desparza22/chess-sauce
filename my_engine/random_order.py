import chess
from my_engine.search_order import SearchOrder

class RandomOrder(SearchOrder):
    def __init__(self):
        pass
    
    def update_priors(self, sorted_moves : list[chess.Move]) -> None:
        pass
    
    def order_moves(self, b:chess.Board) -> list[chess.Move]:
        return [move for move in b.legal_moves]