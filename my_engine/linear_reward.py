import chess
from my_engine.search_order import SearchOrder
from line_profiler import profile

def score_add(place: int) -> int:
    return 3000 - (place * 150)
    
# treat unexplored moves as being 16th best move 
# (some bias towards new moves)
def default_score() -> tuple[int, int]:
    return (score_add(5), 1)

class LinearReward(SearchOrder):
    move_priors : dict[chess.Move, tuple[int, int]]

    def __init__(self):
        self.move_priors = {}
    
    def prior(self, move: chess.Move) -> tuple[int, int]:
        score = self.move_priors.get(move, default_score())
        return score

    def update_priors(self, sorted_moves : list[chess.Move]) -> None:
        for place, move in enumerate(sorted_moves):
            old_prior = self.prior(move)
            add_score = score_add(place)
            self.move_priors[move] = (old_prior[0] + add_score, old_prior[1] + 1)
    
    @profile
    def order_moves(self, b:chess.Board) -> list[chess.Move]:
        moves : list[tuple[chess.Move, tuple[int, int]]] = \
            [(move, self.prior(move)) for move in b.legal_moves]
        sorted_moves = sorted(moves, 
                              key = lambda x: x[1][0] // x[1][1], 
                              reverse=True)
        
        return [sorted_move[0] for sorted_move in sorted_moves]