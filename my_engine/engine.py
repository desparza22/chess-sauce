import chess
from dataclasses import dataclass
from typing import Optional, Tuple, Union, Literal
from line_profiler import profile
from enum import Enum

from my_engine import eval
from my_engine.search_order import SearchOrder
from my_engine.linear_reward import LinearReward
from my_engine.random_order import RandomOrder
from my_engine.quit_early import QuitEarly

worst_white_score, worst_black_score = -1_000_000_000, 1_000_000_000

move_improvement : dict[chess.Move, float] = {}

class Stats:
    moves_at_depth: list[int]
    opt_moves_at_depth: list[int]
    explorations_at_depth: list[int]

    #extensions and moves_post_extensions should be ints instead of length 1
    #lists
    extensions: list[int]
    moves_post_extensions: list[int]
    original_interesting_moves_to_extend_for: int
    def __init__(self, original_interesting_moves_to_extend_for:int):
        self.moves_at_depth = [0 for _ in range(20)]
        self.opt_moves_at_depth = [0 for _ in range(20)]
        self.explorations_at_depth = [0 for _ in range(20)]
        self.extensions = [0]
        self.moves_post_extensions = [0]
        self.original_interesting_moves_to_extend_for = original_interesting_moves_to_extend_for

    @staticmethod
    def print_two_dec(l: list[float]) -> None:
        print([f"{num:.2f}" for num in l])
        
    def print(self) -> None:
        avg_moves_at_depth = [m / e for m, e in zip(self.moves_at_depth, self.explorations_at_depth)] 
        avg_opt_moves_at_depth = [m / e for m, e in zip(self.opt_moves_at_depth, self.explorations_at_depth)] 
        Stats.print_two_dec(avg_moves_at_depth)
        Stats.print_two_dec(avg_opt_moves_at_depth)
        print(self.explorations_at_depth)
        print(self.extensions)
        print(self.moves_post_extensions)

class SearchEvals(Enum):
    # We have a list of moves and evals to return. This is the standard case.
    OK = "OK"
    
    # When we're exploring a position where white/black is already mated, or
    # their position is so bad it's not worth continuing
    LOSS = "LOSS"

    # Exploring a position that is at stalement (we should also check 50 move).
    DRAW = "DRAW"

MovesAndEvals = Union[Tuple[Literal[SearchEvals.OK], list[Tuple[chess.Move, float]]],
                      Tuple[Literal[SearchEvals.LOSS], chess.Color],
                      Tuple[Literal[SearchEvals.DRAW], None]]
             
def eval_moves_and_evals(moves_and_evals: MovesAndEvals) -> float:
    if moves_and_evals[0] == SearchEvals.DRAW:
        return 0.
    if moves_and_evals[0] == SearchEvals.LOSS:
        if moves_and_evals[1] == chess.WHITE:
            return worst_white_score
        return worst_black_score
    return moves_and_evals[1][0][1]


@dataclass
class SearchRes:
    sorted_moves : MovesAndEvals
    positions_explored : int

@dataclass 
class CalcParams:
    move_depth: int
    white_can_get: float
    black_can_get: float
    distance_from_root: int
    interesting_moves_to_extend_for: int


def better_eval(a: Optional[float], b: Optional[float], color: chess.Color) -> int:
    if a is None:
        return 1
    if b is None:
        return -1
    multiplier = 1 if color == chess.WHITE else -1
    if ((a * multiplier) > (b * multiplier)):
        return -1
    else:
        return 1

# returns next_depth, next_interesting_moves_to_extend_for
def extend_for_interesting_moves(b:chess.Board, move:chess.Move, next_depth:int, interesting_moves_to_extend_for:int, distance_from_root:int) -> Tuple[int, int]:
    next_interesting_moves_to_extend_for = interesting_moves_to_extend_for
    if b.is_capture(move):
        if next_depth < 8:
            if next_interesting_moves_to_extend_for > 0:
                next_depth = 8
                next_interesting_moves_to_extend_for -= 1
            else:
                next_depth = 1
    return (next_depth, next_interesting_moves_to_extend_for)

def early_ret(b:chess.Board, distance_from_root:int, quit_early:QuitEarly, positions_explored:int) -> Optional[SearchRes]:
    # does [b.turn] flip if there's checkmate? if not, this needs to be fixed
    if (distance_from_root >= 4 and quit_early.should_quit_early(b)) or b.is_checkmate():
        return SearchRes((SearchEvals.LOSS, b.turn), positions_explored)

    elif b.is_stalemate():
        return SearchRes((SearchEvals.DRAW, None), positions_explored)

    return None
    
# returns eval and positions_explored
def explore_move(b: chess.Board, 
                 move: chess.Move, 
                 prev_calc_params: CalcParams,
                 sibling_move_count: int,
                 quit_early: QuitEarly,
                 search_order: SearchOrder,
                 repeat_moves: dict[str, SearchRes],
                 stats:Stats) -> Tuple[float, int]:
    next_depth = prev_calc_params.move_depth // sibling_move_count
    next_depth, next_interesting_moves_to_extend_for = \
        extend_for_interesting_moves(b, 
                                     move, 
                                     next_depth, 
                                     prev_calc_params.interesting_moves_to_extend_for, 
                                     prev_calc_params.distance_from_root)
    is_first_extension = \
        next_interesting_moves_to_extend_for == \
            prev_calc_params.interesting_moves_to_extend_for - 1 and \
            prev_calc_params.interesting_moves_to_extend_for == \
                stats.original_interesting_moves_to_extend_for
    if next_interesting_moves_to_extend_for < prev_calc_params.interesting_moves_to_extend_for:
        stats.extensions[0] += 1
            
    b.push(move)
    if next_depth <= 0:
        next_score = eval.eval(b)
        res = (next_score, 1)
    else:
        params = CalcParams(next_depth, 
                            prev_calc_params.white_can_get, 
                            prev_calc_params.black_can_get, 
                            prev_calc_params.distance_from_root+1,
                            next_interesting_moves_to_extend_for)
        search_res = calc_best_move(b, 
                                    params,
                                    quit_early,
                                    search_order,
                                    repeat_moves,
                                    stats)
#                             next_depth, 
#                             prev_calc_params.white_can_get, 
#                             prev_calc_params.black_can_get,
#                             prev_calc_params.quit_early,
#                             prev_calc_params.distance_from_root + 0,
#                             next_interesting_moves_to_extend_for,
#                             prev_calc_params.search_order,
#                             prev_calc_params.repeat_moves,
#                             stats)
        if is_first_extension:
            stats.moves_post_extensions[0] += search_res.positions_explored
        res = (eval_moves_and_evals(search_res.sorted_moves), search_res.positions_explored)
    b.pop()
    return res

@profile
def calc_best_move(b: chess.Board,
                   params: CalcParams,
                   quit_early: QuitEarly,
                   search_order: SearchOrder,
                   repeat_moves: dict[str, SearchRes],
                   stats: Stats) -> SearchRes:
    positions_explored = 0
    pos_fen : Optional[str] = None
    if params.distance_from_root >= 3 and params.distance_from_root <= 6:
        pos_fen = b.fen()
        if pos_fen in repeat_moves:
            search_res = repeat_moves[pos_fen]
            return SearchRes(search_res.sorted_moves, positions_explored)
    
    quit_early_res = early_ret(b, params.distance_from_root, quit_early, positions_explored)
    if quit_early_res:
        # don't need to hash these cases
        return quit_early_res

    best_moves : list[tuple[chess.Move, float]] = []
    best_move = None
    best_score = None
    ordered_moves = search_order.order_moves(b)
    stats.moves_at_depth[params.distance_from_root] += len(ordered_moves)
    stats.explorations_at_depth[params.distance_from_root] += 1
    early_break = None
    white_can_get = params.white_can_get
    black_can_get = params.black_can_get
    for idx, move in enumerate(ordered_moves[:params.move_depth]):
        calc_params = CalcParams(params.move_depth, 
                                 white_can_get, 
                                 black_can_get, 
                                 params.distance_from_root, 
                                 params.interesting_moves_to_extend_for)
        next_score, additional_positions_explored = \
            explore_move(b, 
                         move, 
                         calc_params, 
                         len(ordered_moves), 
                         quit_early, 
                         search_order, 
                         repeat_moves, 
                         stats)
        positions_explored += additional_positions_explored
        best_moves.append((move, next_score))
        if better_eval(next_score, best_score, b.turn) < 0:
            best_move = move
            best_score = next_score
            if b.turn == chess.WHITE and \
                better_eval(next_score, white_can_get, chess.WHITE) < 0:
                white_can_get = next_score
            elif b.turn == chess.BLACK and \
                better_eval(next_score, black_can_get, chess.BLACK) < 0:
                black_can_get = next_score
            if white_can_get >= black_can_get:
                early_break = idx + 1
                break

    if early_break:
        stats.opt_moves_at_depth[params.distance_from_root] += early_break
    else:
        stats.opt_moves_at_depth[params.distance_from_root] += len(ordered_moves)
            
    if best_moves is []:
        raise ValueError(b)
    else:
        reverse = b.turn == chess.WHITE
        sorted_moves = sorted(best_moves, key=lambda x: x[1], reverse=reverse)
        search_order.update_priors([x[0] for x in sorted_moves])
        search_res = SearchRes((SearchEvals.OK, sorted_moves), positions_explored)
        if pos_fen:
            repeat_moves[pos_fen] = search_res
        return search_res
    
def go(b: chess.Board, move_depth: int, linear: bool = True) -> SearchRes:
    if linear:
        search_order : SearchOrder = LinearReward()
    else:
        search_order = RandomOrder()
    
    interesting_moves_to_extend_for = 4
    stats = Stats(interesting_moves_to_extend_for)
    depth_from_root = 0
    repeat_moves : dict[str, SearchRes] = {}
    #repeat_moves_pre_search : dict[str, SearchRes] = {}
    #params_pre_search = CalcParams(move_depth//3, worst_white_score, worst_black_score, depth_from_root, interesting_moves_to_extend_for)
    params = CalcParams(move_depth, worst_white_score, worst_black_score, depth_from_root, interesting_moves_to_extend_for)
    quit_early = QuitEarly(b)
    # a mini search to prepopulate search_order
    #_ = calc_best_move(b, params_pre_search, quit_early, search_order, repeat_moves_pre_search, stats)
    res = calc_best_move(b,
                         params,
                         quit_early,
                         search_order,
                         repeat_moves,
                         stats)
    #stats.print()
    return res