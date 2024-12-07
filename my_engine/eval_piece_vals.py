import chess
from line_profiler import profile
from typing import Tuple

# https://www.chessprogramming.org/PeSTO%27s_Evaluation_Function
mg_base_value : dict[chess.PieceType, int] = { chess.PAWN:82, chess.KNIGHT:337, chess.BISHOP:365, chess.ROOK:477, chess.QUEEN:1025,  chess.KING:0 }
eg_base_value : dict[chess.PieceType, int] = { chess.PAWN:94, chess.KNIGHT:281, chess.BISHOP:297, chess.ROOK:512,  chess.QUEEN:936,  chess.KING:0 }

mg_pawn_table= [
      0,   0,   0,   0,   0,   0,  0,   0,
     98, 134,  61,  95,  68, 126, 34, -11,
     -6,   7,  26,  31,  65,  56, 25, -20,
    -14,  13,   6,  21,  23,  12, 17, -23,
    -27,  -2,  -5,  12,  17,   6, 10, -25,
    -26,  -4,  -4, -10,   3,   3, 33, -12,
    -35,  -1, -20, -23, -15,  24, 38, -22,
      0,   0,   0,   0,   0,   0,  0,   0,
]

eg_pawn_table= [
      0,   0,   0,   0,   0,   0,   0,   0,
    178, 173, 158, 134, 147, 132, 165, 187,
     94, 100,  85,  67,  56,  53,  82,  84,
     32,  24,  13,   5,  -2,   4,  17,  17,
     13,   9,  -3,  -7,  -7,  -8,   3,  -1,
      4,   7,  -6,   1,   0,  -5,  -1,  -8,
     13,   8,   8,  10,  13,   0,   2,  -7,
      0,   0,   0,   0,   0,   0,   0,   0,
]

mg_knight_table= [
    -167, -89, -34, -49,  61, -97, -15, -107,
     -73, -41,  72,  36,  23,  62,   7,  -17,
     -47,  60,  37,  65,  84, 129,  73,   44,
      -9,  17,  19,  53,  37,  69,  18,   22,
     -13,   4,  16,  13,  28,  19,  21,   -8,
     -23,  -9,  12,  10,  19,  17,  25,  -16,
     -29, -53, -12,  -3,  -1,  18, -14,  -19,
    -105, -21, -58, -33, -17, -28, -19,  -23,
]

eg_knight_table= [
    -58, -38, -13, -28, -31, -27, -63, -99,
    -25,  -8, -25,  -2,  -9, -25, -24, -52,
    -24, -20,  10,   9,  -1,  -9, -19, -41,
    -17,   3,  22,  22,  22,  11,   8, -18,
    -18,  -6,  16,  25,  16,  17,   4, -18,
    -23,  -3,  -1,  15,  10,  -3, -20, -22,
    -42, -20, -10,  -5,  -2, -20, -23, -44,
    -29, -51, -23, -15, -22, -18, -50, -64,
]

mg_bishop_table= [
    -29,   4, -82, -37, -25, -42,   7,  -8,
    -26,  16, -18, -13,  30,  59,  18, -47,
    -16,  37,  43,  40,  35,  50,  37,  -2,
     -4,   5,  19,  50,  37,  37,   7,  -2,
     -6,  13,  13,  26,  34,  12,  10,   4,
      0,  15,  15,  15,  14,  27,  18,  10,
      4,  15,  16,   0,   7,  21,  33,   1,
    -33,  -3, -14, -21, -13, -12, -39, -21,
]

eg_bishop_table= [
    -14, -21, -11,  -8, -7,  -9, -17, -24,
     -8,  -4,   7, -12, -3, -13,  -4, -14,
      2,  -8,   0,  -1, -2,   6,   0,   4,
     -3,   9,  12,   9, 14,  10,   3,   2,
     -6,   3,  13,  19,  7,  10,  -3,  -9,
    -12,  -3,   8,  10, 13,   3,  -7, -15,
    -14, -18,  -7,  -1,  4,  -9, -15, -27,
    -23,  -9, -23,  -5, -9, -16,  -5, -17,
]

mg_rook_table= [
     32,  42,  32,  51, 63,  9,  31,  43,
     27,  32,  58,  62, 80, 67,  26,  44,
     -5,  19,  26,  36, 17, 45,  61,  16,
    -24, -11,   7,  26, 24, 35,  -8, -20,
    -36, -26, -12,  -1,  9, -7,   6, -23,
    -45, -25, -16, -17,  3,  0,  -5, -33,
    -44, -16, -20,  -9, -1, 11,  -6, -71,
    -19, -13,   1,  17, 16,  7, -37, -26,
]

eg_rook_table= [
    13, 10, 18, 15, 12,  12,   8,   5,
    11, 13, 13, 11, -3,   3,   8,   3,
     7,  7,  7,  5,  4,  -3,  -5,  -3,
     4,  3, 13,  1,  2,   1,  -1,   2,
     3,  5,  8,  4, -5,  -6,  -8, -11,
    -4,  0, -5, -1, -7, -12,  -8, -16,
    -6, -6,  0,  2, -9,  -9, -11,  -3,
    -9,  2,  3, -1, -5, -13,   4, -20,
]

mg_queen_table= [
    -28,   0,  29,  12,  59,  44,  43,  45,
    -24, -39,  -5,   1, -16,  57,  28,  54,
    -13, -17,   7,   8,  29,  56,  47,  57,
    -27, -27, -16, -16,  -1,  17,  -2,   1,
     -9, -26,  -9, -10,  -2,  -4,   3,  -3,
    -14,   2, -11,  -2,  -5,   2,  14,   5,
    -35,  -8,  11,   2,   8,  15,  -3,   1,
     -1, -18,  -9,  10, -15, -25, -31, -50,
]

eg_queen_table= [
     -9,  22,  22,  27,  27,  19,  10,  20,
    -17,  20,  32,  41,  58,  25,  30,   0,
    -20,   6,   9,  49,  47,  35,  19,   9,
      3,  22,  24,  45,  57,  40,  57,  36,
    -18,  28,  19,  47,  31,  34,  39,  23,
    -16, -27,  15,   6,   9,  17,  10,   5,
    -22, -23, -30, -16, -16, -23, -36, -32,
    -33, -28, -22, -43,  -5, -32, -20, -41,
]

mg_king_table= [
    -65,  23,  16, -15, -56, -34,   2,  13,
     29,  -1, -20,  -7,  -8,  -4, -38, -29,
     -9,  24,   2, -16, -20,   6,  22, -22,
    -17, -20, -12, -27, -30, -25, -14, -36,
    -49,  -1, -27, -39, -46, -44, -33, -51,
    -14, -14, -22, -46, -44, -30, -15, -27,
      1,   7,  -8, -64, -43, -16,   9,   8,
    -15,  36,  12, -54,   8, -28,  24,  14,
]

eg_king_table= [
    -74, -35, -18, -18, -11,  15,   4, -17,
    -12,  17,  14,  17,  17,  38,  23,  11,
     10,  17,  23,  15,  20,  45,  44,  13,
     -8,  22,  24,  27,  26,  33,  26,   3,
    -18,  -4,  21,  24,  27,  23,   9, -11,
    -19,  -3,  11,  21,  23,  16,   7,  -9,
    -27, -11,   4,  13,  14,   4,  -5, -17,
    -53, -34, -21, -11, -28, -14, -24, -43
]

mg_tables = {
    chess.PAWN:mg_pawn_table, 
    chess.ROOK:mg_rook_table, 
    chess.KNIGHT:mg_knight_table,
    chess.BISHOP:mg_bishop_table,
    chess.QUEEN:mg_queen_table,
    chess.KING:mg_king_table
}

eg_tables = {
    chess.PAWN:eg_pawn_table, 
    chess.ROOK:eg_rook_table, 
    chess.KNIGHT:eg_knight_table,
    chess.BISHOP:eg_bishop_table,
    chess.QUEEN:eg_queen_table,
    chess.KING:eg_king_table
}

@profile
def piece_values(square:chess.Square, piece:chess.Piece) -> tuple[float, float]:
    mg_base = mg_base_value[piece.piece_type]
    eg_base = eg_base_value[piece.piece_type]
    mg_add_table = mg_tables[piece.piece_type] 
    eg_add_table = eg_tables[piece.piece_type]
    mult = 1
    if piece.color == chess.BLACK:
        square = chess.square_mirror(square)
        mult = -1
    position = (7 - chess.square_rank(square)) + chess.square_file(square)
    mg_add = mg_add_table[position]
    eg_add = eg_add_table[position]
    return (mg_base + mg_add) * mult, (eg_base + eg_add) * mult

@profile
def piece_value(square:chess.Square, piece:chess.Piece, mg_eg_ratio:float) -> float:
    mg_score, eg_score = piece_values(square, piece)
    return (mg_score * mg_eg_ratio) + (eg_score * (1. - mg_eg_ratio))

game_phase_table : dict[chess.PieceType, int] =\
    {chess.PAWN:0, chess.KNIGHT:1, chess.BISHOP:1, chess.ROOK:2, chess.QUEEN:4, chess.KING:0}
@profile
def game_phase(squares_and_pieces: list[Tuple[chess.Square, chess.Piece]]) -> float:
    totals = [game_phase_table[piece.piece_type] for _, piece in squares_and_pieces]
    res = float(sum(totals)) / 24.
    return res
    
@profile
def eval_piece_vals(b: chess.Board) -> tuple[float, float]:
    squares_and_pieces = b.piece_map().items()
    mg_eg_ratio = game_phase(squares_and_pieces)
    scores = [piece_value(square, piece, mg_eg_ratio) for square, piece in squares_and_pieces]
    return sum(scores), mg_eg_ratio

@profile
def diff(b:chess.Board, move:chess.Move, game_phase:float) -> tuple[float, float]:
    game_phase_diff = 0.
    mg_piece_evals = 0.
    eg_piece_evals = 0.
    start_piece = b.piece_at(move.from_square)
    assert start_piece is not None
    if (end_type := move.promotion):
        game_phase_diff -= game_phase_table[start_piece.piece_type]
        game_phase_diff += game_phase_table[end_type]
    else:
        end_type = start_piece.piece_type
    mg_start, eg_start = piece_values(move.from_square, start_piece)
    mg_end, eg_end = piece_values(move.to_square, chess.Piece(end_type, b.turn))
    mg_piece_evals -= mg_start
    eg_piece_evals -= eg_start
    mg_piece_evals += mg_end
    eg_piece_evals += eg_end
    #print(mg_start, eg_start, mg_end, eg_end)
    
    if b.is_capture(move):
        end_rank = chess.square_rank(move.to_square)
        capture_file = chess.square_file(move.to_square)
        if b.is_en_passant(move):
            capture_rank = 3 if end_rank == 2 else 4
        else:
            capture_rank = end_rank

        capture_square = chess.square(capture_file, capture_rank)
        captured_piece = b.piece_at(capture_square)
        if not captured_piece:
            raise ValueError(b, move, b.is_en_passant(move), capture_file, capture_rank)
        mg_captured, eg_captured = piece_values(capture_square, captured_piece)
        #print(mg_captured, eg_captured)
        mg_piece_evals -= mg_captured
        eg_piece_evals -= eg_captured
        game_phase_diff -= game_phase_table[captured_piece.piece_type]
        
    #print(mg_piece_evals, eg_piece_evals)
    game_phase_diff /= 24.
    updated_game_phase = game_phase + game_phase_diff
    piece_evals_diff = \
        updated_game_phase * mg_piece_evals + \
        (1. - updated_game_phase) * eg_piece_evals
    return (piece_evals_diff, game_phase_diff)