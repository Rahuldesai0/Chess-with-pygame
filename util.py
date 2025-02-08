import pygame
import os

# Constants
BOARD_SIZE = 640  # Board size
MARGIN_WIDTH = 300  # More margin on the width
MARGIN_HEIGHT = 50  # Little margin on the height
WINDOW_WIDTH = BOARD_SIZE + 2 * MARGIN_WIDTH
WINDOW_HEIGHT = BOARD_SIZE + 2 * MARGIN_HEIGHT
SQUARE_SIZE = BOARD_SIZE // 8

# Colors
LIGHT_BROWN = (205, 133, 63)
DARK_BROWN = (139, 69, 19)
TEXT_COLOR = (255, 255, 255)
BACKGROUND_COLOR = (127, 127, 127)
HIGHLIGHT_COLOR = (255, 0, 0)      # Red for legal moves
SELECTED_COLOR = (255, 165, 0)     # Orange for selected piece
CHECK_COLOR = (255, 0, 0)          # Red for check indicator
FONT_SIZE = 24

# Piece images directory
PIECE_FOLDER = "pieces"

# Chessboard representation
EMPTY = 0
WHITE = 8
BLACK = 16
PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6

PROMOTION_PIECES = [QUEEN, ROOK, BISHOP, KNIGHT]
PROMOTION_CODES = {
    QUEEN: 'Q',
    ROOK: 'R',
    BISHOP: 'B',
    KNIGHT: 'N'
}
PROMOTION_SIZE = SQUARE_SIZE * 2

CAPTURED_PIECE_SIZE = SQUARE_SIZE // 2
PIECE_VALUES = {
    PAWN: 1,
    KNIGHT: 3,
    BISHOP: 3,
    ROOK: 5,
    QUEEN: 9
}

pygame.mixer.init()
move_sound = pygame.mixer.Sound(os.path.join("audio", "move.mp3"))
capture_sound = pygame.mixer.Sound(os.path.join("audio", "capture.mp3"))
check_sound = pygame.mixer.Sound(os.path.join("audio", "check.mp3"))
checkmate_sound = pygame.mixer.Sound(os.path.join("audio", "checkmate.mp3"))


# Piece mapping for FEN
fen_piece_map = {
    'P': WHITE | PAWN, 'N': WHITE | KNIGHT, 'B': WHITE | BISHOP, 'R': WHITE | ROOK, 'Q': WHITE | QUEEN, 'K': WHITE | KING,
    'p': BLACK | PAWN, 'n': BLACK | KNIGHT, 'b': BLACK | BISHOP, 'r': BLACK | ROOK, 'q': BLACK | QUEEN, 'k': BLACK | KING
}

reverse_fen_map = {v: k for k, v in fen_piece_map.items()}

CASTLING_ROOK_MOVES = {
    (7, 4): {  # White king
        (7, 6): ((7, 7), (7, 5)),  # Kingside: (rook_from, rook_to)
        (7, 2): ((7, 0), (7, 3))   # Queenside
    },
    (0, 4): {  # Black king
        (0, 6): ((0, 7), (0, 5)),
        (0, 2): ((0, 0), (0, 3))
    }
}


def load_board_from_fen(fen):
    global board
    board = [[EMPTY] * 8 for _ in range(8)]
    rows = fen.split()[0].split('/')
    
    for row_idx, row in enumerate(rows):
        col_idx = 0
        for char in row:
            if char.isdigit():
                col_idx += int(char)  # Empty squares
            else:
                board[row_idx][col_idx] = fen_piece_map[char]
                col_idx += 1

def generate_fen(board, active_color, castling_rights, en_passant_target, halfmove=0, fullmove=1):
    fen_rows = []
    for row in board:
        empty_count = 0
        fen_row = ""
        for piece in row:
            if piece == EMPTY:
                empty_count += 1
            else:
                if empty_count > 0:
                    fen_row += str(empty_count)
                    empty_count = 0
                fen_row += reverse_fen_map[piece]
        if empty_count > 0:
            fen_row += str(empty_count)
        fen_rows.append(fen_row)
    ep = '-' if en_passant_target is None else get_algebraic_notation(en_passant_target[0], en_passant_target[1])
    return "/".join(fen_rows) + f" {active_color} {castling_rights} {ep} {halfmove} {fullmove}"

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

# Default starting position FEN
starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
load_board_from_fen(starting_fen)

def load_pieces():
    pieces = {}
    small_pieces = {}
    piece_map = {
        WHITE | PAWN: "wp", WHITE | KNIGHT: "wn", WHITE | BISHOP: "wb", WHITE | ROOK: "wr", WHITE | QUEEN: "wq", WHITE | KING: "wk",
        BLACK | PAWN: "bp", BLACK | KNIGHT: "bn", BLACK | BISHOP: "bb", BLACK | ROOK: "br", BLACK | QUEEN: "bq", BLACK | KING: "bk"
    }
    for code, name in piece_map.items():
        path = os.path.join(PIECE_FOLDER, f"{name}.png")
        image = pygame.image.load(path)
        pieces[code] = pygame.transform.smoothscale(image, (SQUARE_SIZE, SQUARE_SIZE))
        small_pieces[code] = pygame.transform.smoothscale(image, (CAPTURED_PIECE_SIZE, CAPTURED_PIECE_SIZE))
    return pieces, small_pieces

def get_algebraic_notation(row, col):
    return f"{chr(97 + col)}{8 - row}"

def print_move_notation(selected_piece, start_pos, end_pos, capture):
    piece_symbol = reverse_fen_map[selected_piece].upper()
    start_row, start_col = start_pos
    end_row, end_col = end_pos

    # Castling detection
    if piece_symbol == 'K' and abs(end_col - start_col) == 2:
        return "O-O" if end_col > start_col else "O-O-O"

    # Pawn moves
    if piece_symbol == "P":  
        notation = get_algebraic_notation(*end_pos)
        if capture:
            notation = f"{chr(97 + start_col)}x{notation}"
        return notation

    # Other pieces
    notation = piece_symbol
    if capture:
        notation += "x"
    notation += get_algebraic_notation(end_row, end_col)
    return notation

def find_king(board, color):
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece != EMPTY and (piece & 24) == color and (piece & 7) == KING:
                return (r, c)
    return None

def get_castling_rights(board, moved_positions):
    rights = ""
    # For White:
    if (7, 4) not in moved_positions and board[7][4] == (WHITE | KING):
         if (7, 7) not in moved_positions and board[7][7] == (WHITE | ROOK):
              rights += "K"
         if (7, 0) not in moved_positions and board[7][0] == (WHITE | ROOK):
              rights += "Q"
    # For Black:
    if (0, 4) not in moved_positions and board[0][4] == (BLACK | KING):
         if (0, 7) not in moved_positions and board[0][7] == (BLACK | ROOK):
              rights += "k"
         if (0, 0) not in moved_positions and board[0][0] == (BLACK | ROOK):
              rights += "q"
    return rights if rights != "" else "-"


def is_square_under_attack(board, pos, attacker_color, moved_positions, en_passant_target):
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece != EMPTY and (piece & 24) == attacker_color:
                # Do not consider castling moves when checking for attacks.
                moves = get_pseudo_legal_moves(board, (r, c), moved_positions, en_passant_target, ignore_castling=True)
                if pos in moves:
                    return True
    return False


def is_in_check(board, color, moved_positions, en_passant_target):
    king_pos = find_king(board, color)
    if not king_pos:
        return False
    attacker_color = BLACK if color == WHITE else WHITE
    return is_square_under_attack(board, king_pos, attacker_color, moved_positions, en_passant_target)

def get_pseudo_legal_moves(board, pos, moved_positions, en_passant_target=None, ignore_castling=False):
    row, col = pos
    piece = board[row][col]
    if piece == EMPTY:
        return []
    
    piece_type = piece & 7
    color = piece & 24
    moves = []

    def is_valid(r, c):
        if 0 <= r < 8 and 0 <= c < 8:
            target = board[r][c]
            return target == EMPTY or (target & 24) != color
        return False

    # Pawn moves
    if piece_type == PAWN:
        direction = -1 if color == WHITE else 1
        # Normal moves
        if is_valid(row + direction, col) and board[row + direction][col] == EMPTY:
            moves.append((row + direction, col))
            # Double step
            if (color == WHITE and row == 6) or (color == BLACK and row == 1):
                if board[row + 2*direction][col] == EMPTY:
                    moves.append((row + 2*direction, col))
        # Captures
        for dc in [-1, 1]:
            if is_valid(row + direction, col + dc) and board[row + direction][col + dc] != EMPTY:
                moves.append((row + direction, col + dc))
        # En passant captures
        if en_passant_target is not None:
            ep_row, ep_col = en_passant_target
            if (row == ep_row - direction) and (col in [ep_col - 1, ep_col + 1]):
                moves.append((ep_row, ep_col))

    # Knight moves
    elif piece_type == KNIGHT:
        knight_moves = [(-2,-1), (-1,-2), (1,-2), (2,-1),
                        (2,1), (1,2), (-1,2), (-2,1)]
        for dr, dc in knight_moves:
            if is_valid(row + dr, col + dc):
                moves.append((row + dr, col + dc))

    # Bishop moves
    elif piece_type == BISHOP:
        directions = [(-1,-1), (-1,1), (1,-1), (1,1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] == EMPTY:
                    moves.append((r, c))
                else:
                    if (board[r][c] & 24) != color:
                        moves.append((r, c))
                    break
                r += dr
                c += dc

    # Rook moves
    elif piece_type == ROOK:
        directions = [(-1,0), (1,0), (0,-1), (0,1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] == EMPTY:
                    moves.append((r, c))
                else:
                    if (board[r][c] & 24) != color:
                        moves.append((r, c))
                    break
                r += dr
                c += dc

    # Queen moves
    elif piece_type == QUEEN:
        directions = [(-1,-1), (-1,1), (1,-1), (1,1),
                     (-1,0), (1,0), (0,-1), (0,1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] == EMPTY:
                    moves.append((r, c))
                else:
                    if (board[r][c] & 24) != color:
                        moves.append((r, c))
                    break
                r += dr
                c += dc

    # King moves
    elif piece_type == KING:
        # Regular king moves
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                if is_valid(row + dr, col + dc):
                    moves.append((row + dr, col + dc))

        # Only add castling moves if we're not ignoring them.
        if not ignore_castling:
            enemy_color = BLACK if color == WHITE else WHITE
            # The king cannot castle if it is currently in check.
            if is_square_under_attack(board, (row, col), enemy_color, moved_positions, en_passant_target):
                pass  # king in check; skip castling
            elif (row, col) in CASTLING_ROOK_MOVES:
                for castle_end, (rook_from, rook_to) in CASTLING_ROOK_MOVES[(row, col)].items():
                    # Check if the king or rook has moved.
                    if (row, col) in moved_positions or rook_from in moved_positions:
                        continue
                    # Ensure the rook is still in place.
                    if board[rook_from[0]][rook_from[1]] != (color | ROOK):
                        continue

                    # Determine the squares between the king and rook.
                    if castle_end[1] > col:
                        # Kingside castling.
                        between_squares = [(row, col+1), (row, col+2)]
                        king_path = between_squares  # king passes through these squares
                    else:
                        # Queenside castling.
                        between_squares = [(row, col-1), (row, col-2), (row, col-3)]
                        king_path = [(row, col-1), (row, col-2)]  # king passes through these two squares

                    # Ensure the path between king and rook is empty.
                    if any(board[r][c] != EMPTY for (r, c) in between_squares):
                        continue

                    # Ensure none of the squares that the king moves through or lands on are under attack.
                    if any(is_square_under_attack(board, square, enemy_color, moved_positions, en_passant_target)
                           for square in king_path):
                        continue

                    # If all conditions are met, allow the castling move.
                    moves.append(castle_end)

    return moves

def get_legal_moves(board, pos, moved_positions, en_passant_target=None):
    pseudo_moves = get_pseudo_legal_moves(board, pos, moved_positions, en_passant_target)
    legal_moves = []
    original_piece = board[pos[0]][pos[1]]
    original_color = original_piece & 24

    for move in pseudo_moves:
        # Create temporary board state
        temp_board = [row.copy() for row in board]
        start_row, start_col = pos
        end_row, end_col = move
        
        # Make the move
        temp_piece = temp_board[start_row][start_col]
        temp_board[start_row][start_col] = EMPTY
        temp_board[end_row][end_col] = temp_piece

        # Find current king position
        king_pos = find_king(temp_board, original_color)
        if not king_pos:
            continue

        # Check if king is under attack
        attacker_color = BLACK if original_color == WHITE else WHITE
        if not is_square_under_attack(temp_board, king_pos, attacker_color, moved_positions, en_passant_target):
            legal_moves.append(move)

    return legal_moves

def create_initial_board():
    """
    Returns an 8x8 board with the initial chess position.
    Adjust the piece codes based on your own definitions.
    """
    board = [[EMPTY for _ in range(8)] for _ in range(8)]
    
    # Set up Black pieces.
    board[0] = [BLACK | ROOK, BLACK | KNIGHT, BLACK | BISHOP, BLACK | QUEEN,
                BLACK | KING, BLACK | BISHOP, BLACK | KNIGHT, BLACK | ROOK]
    board[1] = [BLACK | PAWN for _ in range(8)]
    
    # Set up White pieces.
    board[6] = [WHITE | PAWN for _ in range(8)]
    board[7] = [WHITE | ROOK, WHITE | KNIGHT, WHITE | BISHOP, WHITE | QUEEN,
                WHITE | KING, WHITE | BISHOP, WHITE | KNIGHT, WHITE | ROOK]
    
    return board
