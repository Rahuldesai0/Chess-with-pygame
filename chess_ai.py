import random
from util import EMPTY, get_legal_moves, WHITE, BLACK, fen_piece_map

def parse_fen(fen):
    """
    Parses a FEN string and returns a tuple:
      (board, active_color, castling, en_passant_target, halfmove, fullmove)
    
    - board: 8x8 list of integers (using your piece codes)
    - active_color: 'w' or 'b'
    - castling: a string of castling rights (e.g., "KQkq" or "-")
    - en_passant_target: a tuple (row, col) or None
    - halfmove: integer (halfmove clock)
    - fullmove: integer (fullmove number)
    """
    parts = fen.split()
    board_str = parts[0]
    active_color = parts[1]
    castling = parts[2]
    en_passant = parts[3]
    halfmove = int(parts[4])
    fullmove = int(parts[5])
    
    board = []
    rows = board_str.split('/')
    for row in rows:
        board_row = []
        for char in row:
            if char.isdigit():
                board_row.extend([EMPTY] * int(char))
            else:
                board_row.append(fen_piece_map[char])
        board.append(board_row)
    
    if en_passant == '-':
        en_passant_target = None
    else:
        # Convert algebraic notation to board coordinates.
        file = ord(en_passant[0]) - ord('a')
        rank = 8 - int(en_passant[1])
        en_passant_target = (rank, file)
    
    return board, active_color, castling, en_passant_target, halfmove, fullmove

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
