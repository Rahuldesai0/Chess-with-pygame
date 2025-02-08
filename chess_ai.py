import random
from util import EMPTY, parse_fen, get_legal_moves, WHITE, BLACK, fen_piece_map

def get_ai_move(fen):
    """
    Takes a FEN string as input and returns a random legal move.
    
    The move is returned as a tuple: ((start_row, start_col), (end_row, end_col)).
    If no legal moves are available, returns None.
    
    Note: Since the FEN string does not include information about moved pieces,
    we pass an empty set for moved_positions. (This may affect special moves like castling.)
    """
    board, active_color, castling, en_passant_target, halfmove, fullmove = parse_fen(fen)
    # For now, we assume that moved_positions is empty.
    moved_positions = set()
    
    # Determine which color is to move.
    color = WHITE if active_color == 'w' else BLACK
    
    legal_moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece != EMPTY and (piece & 24) == color:
                # get_legal_moves is assumed to return a list of destination tuples.
                moves = get_legal_moves(board, (r, c), moved_positions, en_passant_target)
                for move in moves:
                    legal_moves.append(((r, c), move))
    
    if not legal_moves:
        return None
    
    return random.choice(legal_moves)
