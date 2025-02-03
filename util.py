import pygame
import os

# Constants
BOARD_SIZE = 640  # Board size
MARGIN_WIDTH = 300  # More margin on the width
MARGIN_HEIGHT = 30  # Little margin on the height
WINDOW_WIDTH = BOARD_SIZE + 2 * MARGIN_WIDTH
WINDOW_HEIGHT = BOARD_SIZE + 2 * MARGIN_HEIGHT
SQUARE_SIZE = BOARD_SIZE // 8

# Colors
LIGHT_BROWN = (205, 133, 63)
DARK_BROWN = (139, 69, 19)
TEXT_COLOR = (255, 255, 255)
BACKGROUND_COLOR = (0, 0, 0)
HIGHLIGHT_COLOR = (255, 0, 0)      # Red for legal moves
SELECTED_COLOR = (255, 165, 0)     # Orange for selected piece
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

move_sound = pygame.mixer.Sound(os.path.join("audio", "move.mp3"))
capture_sound = pygame.mixer.Sound(os.path.join("audio", "capture.mp3"))

# Piece mapping for FEN
fen_piece_map = {
    'P': WHITE | PAWN, 'N': WHITE | KNIGHT, 'B': WHITE | BISHOP, 'R': WHITE | ROOK, 'Q': WHITE | QUEEN, 'K': WHITE | KING,
    'p': BLACK | PAWN, 'n': BLACK | KNIGHT, 'b': BLACK | BISHOP, 'r': BLACK | ROOK, 'q': BLACK | QUEEN, 'k': BLACK | KING
}

reverse_fen_map = {v: k for k, v in fen_piece_map.items()}

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

def generate_fen():
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
    return "/".join(fen_rows) + " w KQkq - 0 1"

# Default starting position FEN
starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
load_board_from_fen(starting_fen)

def load_pieces():
    pieces = {}
    piece_map = {
        WHITE | PAWN: "wp", WHITE | KNIGHT: "wn", WHITE | BISHOP: "wb", WHITE | ROOK: "wr", WHITE | QUEEN: "wq", WHITE | KING: "wk",
        BLACK | PAWN: "bp", BLACK | KNIGHT: "bn", BLACK | BISHOP: "bb", BLACK | ROOK: "br", BLACK | QUEEN: "bq", BLACK | KING: "bk"
    }
    for code, name in piece_map.items():
        path = os.path.join(PIECE_FOLDER, f"{name}.png")
        image = pygame.image.load(path)
        pieces[code] = pygame.transform.smoothscale(image, (SQUARE_SIZE, SQUARE_SIZE))
    return pieces

def get_algebraic_notation(row, col):
    return f"{chr(97 + col)}{8 - row}"

def print_move_notation(selected_piece, start_pos, end_pos, capture):
    piece_symbol = reverse_fen_map[selected_piece].upper()

    if piece_symbol == "P":  
        notation = get_algebraic_notation(*end_pos)
        if capture:
            notation = f"{chr(97 + start_pos[1])}x{notation}"
    else:
        notation = piece_symbol
        if capture:
            notation += "x"
        notation += get_algebraic_notation(*end_pos)
    
    print("Move played:", notation)
    return notation

def get_legal_moves(board, pos):
    """Calculate all legal moves for a piece at the given position"""
    row, col = pos
    piece = board[row][col]
    if piece == EMPTY:
        return []
    
    piece_type = piece & 7  # Extract piece type
    color = piece & 24      # Extract color
    legal_moves = []

    # Helper function
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
            legal_moves.append((row + direction, col))
            # Double step
            if (color == WHITE and row == 6) or (color == BLACK and row == 1):
                if board[row + 2*direction][col] == EMPTY:
                    legal_moves.append((row + 2*direction, col))
        # Captures
        for dc in [-1, 1]:
            if is_valid(row + direction, col + dc) and board[row + direction][col + dc] != EMPTY:
                legal_moves.append((row + direction, col + dc))

    # Knight moves
    elif piece_type == KNIGHT:
        moves = [(-2,-1), (-1,-2), (1,-2), (2,-1),
                 (2,1), (1,2), (-1,2), (-2,1)]
        for dr, dc in moves:
            if is_valid(row + dr, col + dc):
                legal_moves.append((row + dr, col + dc))

    # Bishop moves
    elif piece_type == BISHOP:
        directions = [(-1,-1), (-1,1), (1,-1), (1,1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] == EMPTY:
                    legal_moves.append((r, c))
                else:
                    if (board[r][c] & 24) != color:
                        legal_moves.append((r, c))
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
                    legal_moves.append((r, c))
                else:
                    if (board[r][c] & 24) != color:
                        legal_moves.append((r, c))
                    break
                r += dr
                c += dc

    # Queen moves
    elif piece_type == QUEEN:
        # Combine rook and bishop moves
        directions = [(-1,-1), (-1,1), (1,-1), (1,1),
                     (-1,0), (1,0), (0,-1), (0,1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] == EMPTY:
                    legal_moves.append((r, c))
                else:
                    if (board[r][c] & 24) != color:
                        legal_moves.append((r, c))
                    break
                r += dr
                c += dc

    # King moves
    elif piece_type == KING:
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                if is_valid(row + dr, col + dc):
                    legal_moves.append((row + dr, col + dc))

    return legal_moves