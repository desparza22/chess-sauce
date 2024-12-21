# Implements the UCI protocol (at least enough of it to play on lichess)
import sys
import chess
from my_engine import engine
from typing import Optional


class Response():
    def __init__(self, quit: bool, output: list[str], board:chess.Board, log:Optional[str]):
        self.quit = quit
        self.output = output
        self.board = board
        self.log = log
        
class Option():
    def __init__(self, name:str, type:str, rest:str):
        self.name = name
        self.type = type
        self.rest = rest
        
    def __str__(self):
        return f"option name {self.name} type {self.type} {self.rest}"

    

options = [Option("Move Overhead", "spin", "default 0"), 
           Option("Threads", "spin", "default 1"),
           Option("Hash", "spin", "default 1")]

def parse_go(input:list[str]) -> dict[str,str]:
    idx = 0
    
    # skip "go"
    idx += 1
    
    fields = {}
    while idx < len(input):
        next_term = input[idx]
        idx += 1
        
        if next_term in ["infinite", "ponder"]:
            fields[next_term] = ""
        elif next_term == "searchmoves":
            fields[next_term] = " ".join(input[idx:])
            idx = len(input)
        elif next_term in ["winc", "binc", "wtime", "btime", 
                           "movestogo", "depth", "nodes", "mate", 
                           "movetime"]:
            value = input[idx]
            idx += 1
            fields[next_term] = value
        else:
            raise ValueError(next_term)
        
    return fields

def position_response(input: list[str]) -> Response:
    if input[1] == "startpos":
        b = chess.Board()
        move_start = 3
    else:
        assert(input[1] == "fen")
        fen = " ".join(input[2:8])
        b = chess.Board(fen)
        move_start = 9

    for move in input[move_start:]:
        b.push(chess.Move.from_uci(move))
    return Response(False, [], b, None)
    
    
def go_response(fields : dict[str, str], b:chess.Board) -> Response:
    depth = 800000
    if "movetime" in fields:
        movetime = max(10000, int(fields["movetime"]))
        depth = int(movetime * 0.7)
    res, _ = engine.go(b, depth)

    log = f"explored: {res.positions_explored}"
    best_move = engine.best_move_of_eval(res.sorted_moves)
    return Response(False, [f"bestmove {chess.Move.uci(best_move)}"], chess.Board(), log)

def dynamic_response(input:list[str], b:chess.Board) -> Response:
    if input[0] == "position":
        return position_response(input)
    elif input[0] == "go":
        return go_response(parse_go(input), b) 
    
    raise ValueError(input)

def create_response(input:list[str], b:chess.Board) -> Response:
    if input[0] == "uci":
        res = ["id name my_bot", "id author diego"] \
            + [str(opt) for opt in options] \
                + ["uciok"]
        return Response(False, res, b, None)
    elif input[0] == "quit":
        return Response(True, [], b, None)
    elif input[0] == "isready":
        return Response(False, ["readyok"], b, None)
    elif input[0] == "ucinewgame":
        return Response(False, [], b, None)
    else:
        return dynamic_response(input, b)

def main(log:str) -> None:
    with open(log, "w+") as f:
        b = chess.Board()
        for input in sys.stdin:
            f.write(input)
            res = create_response(input.strip().split(), b)
            b = res.board
            if not res.quit:
                for line in res.output:
                    f.write(f"# {line}\n")
                    print(line, flush=True)
                f.write(f"+ log + {res.log}\n")
            else:
                exit(0)