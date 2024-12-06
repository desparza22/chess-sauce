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
        self.moves_at_depth = [0 for _ in range(400)]
        self.opt_moves_at_depth = [0 for _ in range(400)]
        self.explorations_at_depth = [0 for _ in range(400)]
        self.extensions = [0]
        self.moves_post_extensions = [0]
        self.original_interesting_moves_to_extend_for = original_interesting_moves_to_extend_for

    @staticmethod
    def print_two_dec(l: list[float]) -> None:
        print([f"{num:.2f}" for num in l])
       
    @staticmethod 
    def safe_div(a: int, b: int) -> float:
        if b == 0:
            if a == 0:
                return 0.
            else:
                return 9999999999.
        return a/b
    
    def print(self) -> None:
        avg_moves_at_depth = [Stats.safe_div(m,e) for m, e in zip(self.moves_at_depth, self.explorations_at_depth)] 
        avg_opt_moves_at_depth = [Stats.safe_div(m,e) for m, e in zip(self.opt_moves_at_depth, self.explorations_at_depth)] 
        print("avg moves at depth:")
        Stats.print_two_dec(avg_moves_at_depth)
        print("avg opt moves at depth")
        Stats.print_two_dec(avg_opt_moves_at_depth)
        print("explorations at depth")
        print(self.explorations_at_depth)
        print("extensions")
        print(self.extensions)
        print("moves post extensions")
        print(self.moves_post_extensions)

class SearchEvals(Enum):
    # We have a list of moves and evals to return. This is the standard case.
    SUBMOVE_LIST = "SUBMOVE_LIST"
    
    # When we're exploring a position where white/black is already mated, or
    # their position is so bad it's not worth continuing
    LOSS = "LOSS"
    
    # White/black has reached a good score, and the opposite color can prevent
    # the game from getting here
    ALPHA_BETA_CROSS = "ALPHA_BETA_CROSS"

    # Reached the end of our search depth.
    LEAF_EVAL = "LEAF_EVAL"

    # Exploring a position that is at stalement (we should also check 50 move).
    DRAW = "DRAW"

EarlyExit = Union[Tuple[Literal[SearchEvals.LOSS], chess.Color],
                  Tuple[Literal[SearchEvals.ALPHA_BETA_CROSS], chess.Color],
                  Tuple[Literal[SearchEvals.DRAW], None]]

# we could make SUBMOVELIST have a list of (move, Eval), but then we'd be
# holding references to every Eval we ecounter and consume a lot of memory
Eval = Union[Tuple[Literal[SearchEvals.SUBMOVE_LIST], list[Tuple[chess.Move, float]]],
             Tuple[Literal[SearchEvals.LEAF_EVAL], float],
             EarlyExit]

             
def eval_early_exit(early_exit: EarlyExit) -> float:
    if early_exit[0] == SearchEvals.DRAW:
        return 0.
    
    if early_exit[0] == SearchEvals.LOSS:
        mult = 1.1
    else:
        assert early_exit[0] == SearchEvals.ALPHA_BETA_CROSS
        mult = -1.
        
    if early_exit[1] == chess.WHITE:
        points = worst_white_score
    else:
        points = worst_black_score
        
    return mult * points
        
def float_of_eval(moves_and_evals: Eval) -> float:
    if moves_and_evals[0] == SearchEvals.SUBMOVE_LIST:
        return moves_and_evals[1][0][1]

    if moves_and_evals[0] == SearchEvals.LEAF_EVAL:
        return moves_and_evals[1]
    
    return eval_early_exit(moves_and_evals)

def compare_evals(a:Eval, b:Eval, color:chess.Color) -> int:
    a_score = float_of_eval(a)
    b_score = float_of_eval(b)
    if a_score > b_score:
        res = -1
    elif a_score == b_score:
        res = 0
    else:
        res = 1
        
    if color == chess.WHITE:
        mult = 1
    else:
        mult = -1
    return res * mult

def print_eval(eval: Eval) -> str:
    if eval[0] == SearchEvals.SUBMOVE_LIST:
        return f"(submove: {float_of_eval(eval)}"
    else:
        return str(eval)

@dataclass
class SearchRes:
    sorted_moves : Eval

    # useful for debugging
    positions_explored : int
    explored : Optional[list[Tuple[chess.Move, Eval]]]

@dataclass 
class CalcParams:
    move_depth: int
    # if we run out of move_depth to explore, ply_depth says how many additional
    # plies to explore
    ply_depth: int
    white_can_get: Eval
    black_can_get: Eval
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

def is_interesting(b:chess.Board, move:chess.Move) -> bool:
    b.push(move)
    is_check = b.is_check()
    b.pop()
    return b.is_capture(move) or is_check


def early_ret(b:chess.Board, distance_from_root:int, quit_early:QuitEarly, positions_explored:int) -> Optional[SearchRes]:
    # does [b.turn] flip if there's checkmate? if not, this needs to be fixed
    if (distance_from_root >= 4 and quit_early.should_quit_early(b)) or b.is_checkmate():
        return SearchRes((SearchEvals.LOSS, b.turn), positions_explored, None)

    elif b.is_stalemate():
        return SearchRes((SearchEvals.DRAW, None), positions_explored, None)

    return None
    
# returns eval and positions_explored
def explore_move(b: chess.Board, 
                 move: chess.Move, 
                 prev_calc_params: CalcParams,
                 sibling_move_count: int,
                 quit_early: QuitEarly,
                 search_order: SearchOrder,
                 repeat_moves: dict[str, SearchRes],
                 stats:Stats,
                 sequence_to_track: Optional[list[chess.Move]]) -> Tuple[Eval, int]:
    next_depth = prev_calc_params.move_depth // sibling_move_count
    next_ply_depth = prev_calc_params.ply_depth
    next_interesting_moves_to_extend_for = prev_calc_params.interesting_moves_to_extend_for
        
    is_first_extension = False
    is_extension = False

    move_is_interesting = is_interesting(b, move)
            
    b.push(move)
    if next_depth <= 0:
        if next_ply_depth == 0:
            if move_is_interesting:
                if next_interesting_moves_to_extend_for > 0:
                    next_interesting_moves_to_extend_for -= 1
                    next_ply_depth = 1
                    is_extension = True
                    is_first_extension = \
                        prev_calc_params.interesting_moves_to_extend_for == \
                        stats.original_interesting_moves_to_extend_for
                is_leaf = False
            else:
                is_leaf = True
        else:
            next_ply_depth -= 1
            is_leaf = False
    else:
        is_leaf = False
            
    if is_leaf:
            next_score = eval.eval(b)
            res : Tuple[Eval, int] = ((SearchEvals.LEAF_EVAL, next_score), 1)
    else:
        params = CalcParams(next_depth,
                            next_ply_depth,
                            prev_calc_params.white_can_get, 
                            prev_calc_params.black_can_get, 
                            prev_calc_params.distance_from_root+1,
                            next_interesting_moves_to_extend_for)
        search_res = calc_best_move(b, 
                                    params,
                                    quit_early,
                                    search_order,
                                    repeat_moves,
                                    stats,
                                    sequence_to_track)

        if is_extension:
            stats.extensions[0] += 1
        if is_first_extension:
            stats.moves_post_extensions[0] += search_res.positions_explored
        res = (search_res.sorted_moves, search_res.positions_explored)
    b.pop()
    return res

@profile
def calc_best_move(b: chess.Board,
                   params: CalcParams,
                   quit_early: QuitEarly,
                   search_order: SearchOrder,
                   repeat_moves: dict[str, SearchRes],
                   stats: Stats,
                   sequence_to_track : Optional[list[chess.Move]]) -> SearchRes:
    positions_explored = 0
    pos_fen : Optional[str] = None
    if params.distance_from_root >= 3 and params.distance_from_root <= 6:
        pos_fen = b.fen()
        if pos_fen in repeat_moves:
            search_res = repeat_moves[pos_fen]
            return SearchRes(search_res.sorted_moves, positions_explored, None)
    
    quit_early_res = early_ret(b, params.distance_from_root, quit_early, positions_explored)
    if quit_early_res:
        # don't need to hash these cases
        return quit_early_res

    explored_moves : list[Tuple[chess.Move, Eval]] = []
    ordered_moves = search_order.order_moves(b)
    stats.moves_at_depth[params.distance_from_root] += len(ordered_moves)
    stats.explorations_at_depth[params.distance_from_root] += 1
    early_break = None
    white_can_get = params.white_can_get
    black_can_get = params.black_can_get
    if sequence_to_track:
        print(f"move depth: {params.move_depth}")
        print(f"available moves: {len(ordered_moves)}")
    for idx, move in enumerate(ordered_moves):
        if sequence_to_track is not None and len(sequence_to_track) > 0 and move == sequence_to_track[0]:
            next_sequence_to_track = sequence_to_track[1:]
            print(f"exploring {move}", flush=True)
        else:
            next_sequence_to_track = None
        calc_params = CalcParams(params.move_depth, 
                                 params.ply_depth,
                                 white_can_get, 
                                 black_can_get, 
                                 params.distance_from_root, 
                                 params.interesting_moves_to_extend_for)
        next_eval, additional_positions_explored = \
            explore_move(b, 
                         move, 
                         calc_params, 
                         len(ordered_moves), 
                         quit_early, 
                         search_order, 
                         repeat_moves, 
                         stats,
                         next_sequence_to_track)
        positions_explored += additional_positions_explored
        explored_moves.append((move, next_eval))
        if b.turn == chess.WHITE and \
            compare_evals(next_eval, white_can_get, chess.WHITE) < 0:
            white_can_get = next_eval
        elif b.turn == chess.BLACK and \
            compare_evals(next_eval, black_can_get, chess.BLACK) < 0:
            black_can_get = next_eval
        if compare_evals(white_can_get, black_can_get, chess.WHITE) < 0:
            early_break = idx + 1
            break

    if early_break:
        stats.opt_moves_at_depth[params.distance_from_root] += early_break
    else:
        stats.opt_moves_at_depth[params.distance_from_root] += len(ordered_moves)
            
    if explored_moves is []:
        raise ValueError(b)
    else:
        reverse = b.turn == chess.WHITE
        sorted_explored_moves = sorted(explored_moves, key=lambda x: float_of_eval(x[1]), reverse=reverse)
        search_order.update_priors([x[0] for x in sorted_explored_moves])
        if early_break is None:
            sorted_moves_evalled = [(x[0], float_of_eval(x[1])) for x in sorted_explored_moves]
            sorted_moves : Eval = (SearchEvals.SUBMOVE_LIST, sorted_moves_evalled)
        else:
            sorted_moves = (SearchEvals.ALPHA_BETA_CROSS, b.turn)
        search_res = SearchRes(sorted_moves, positions_explored, sorted_explored_moves)
        if pos_fen:
            repeat_moves[pos_fen] = search_res
        return search_res
    
def go(b: chess.Board, move_depth: int, quick: bool, linear: bool = True) -> SearchRes:
    if linear:
        search_order : SearchOrder = LinearReward()
    else:
        search_order = RandomOrder()
    
    interesting_moves_to_extend_for = 0 if quick else 1
    stats = Stats(interesting_moves_to_extend_for)
    depth_from_root = 0
    repeat_moves : dict[str, SearchRes] = {}
    ply_depth = 0
    #repeat_moves_pre_search : dict[str, SearchRes] = {}
    #params_pre_search = CalcParams(move_depth//3, worst_white_score, worst_black_score, depth_from_root, interesting_moves_to_extend_for)
    params = CalcParams(move_depth, 
                        ply_depth,
                        (SearchEvals.LOSS, chess.WHITE), 
                        (SearchEvals.LOSS, chess.BLACK), 
                        depth_from_root, 
                        interesting_moves_to_extend_for)
    quit_early = QuitEarly(b)
    # a mini search to prepopulate search_order
    #_ = calc_best_move(b, params_pre_search, quit_early, search_order, repeat_moves_pre_search, stats)
    #sequence_to_track = [chess.Move.from_uci(uci) for uci in ["g1e3", "d8d1", "e3c1", "f6g5"]]
    sequence_to_track = None
    res = calc_best_move(b,
                         params,
                         quit_early,
                         search_order,
                         repeat_moves,
                         stats,
                         sequence_to_track)
    #stats.print()
    return res