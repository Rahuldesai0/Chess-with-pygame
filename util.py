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

def generate_fen(en_passant_target=None):
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
    en_passant_square = '-' if en_passant_target is None else get_algebraic_notation(en_passant_target[0], en_passant_target[1])
    return "/".join(fen_rows) + f" w KQkq {en_passant_square} 0 1"

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

def is_square_under_attack(board, pos, attacker_color, moved_positions, en_passant_target):
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece != EMPTY and (piece & 24) == attacker_color:
                moves = get_pseudo_legal_moves(board, (r, c), moved_positions, en_passant_target)
                if pos in moves:
                    return True
    return False

def is_in_check(board, color, moved_positions, en_passant_target):
    king_pos = find_king(board, color)
    if not king_pos:
        return False
    attacker_color = BLACK if color == WHITE else WHITE
    return is_square_under_attack(board, king_pos, attacker_color, moved_positions, en_passant_target)

def get_pseudo_legal_moves(board, pos, moved_positions, en_passant_target=None):
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
        # Regular moves
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                if is_valid(row + dr, col + dc):
                    moves.append((row + dr, col + dc))

        # Castling
        king_pos = (row, col)
        if king_pos in CASTLING_ROOK_MOVES:
            for castle_end, (rook_from, rook_to) in CASTLING_ROOK_MOVES[king_pos].items():
                if king_pos in moved_positions or rook_from in moved_positions:
                    continue
                if (board[rook_from[0]][rook_from[1]] == (color | ROOK) and 
                    all(board[r][c] == EMPTY for (r,c) in [rook_from, (row, (col+rook_from[1])//2), castle_end] if (r,c) != rook_from)):
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
