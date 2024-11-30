import chess
from abc import ABC, abstractmethod

class SearchOrder(ABC):

    @abstractmethod
    def update_priors(self, sorted_moves : list[chess.Move]) -> None:
        pass
    
    @abstractmethod
    def order_moves(self, b:chess.Board) -> list[chess.Move]:
        pass