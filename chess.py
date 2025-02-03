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

pygame.mixer.init()
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

HIGHLIGHT_COLOR = (255, 0, 0)      # Red for legal moves
SELECTED_COLOR = (255, 165, 0)     # Orange for selected piece

def draw_board(win, legal_moves=None, selected_pos=None):
    font = pygame.font.Font(None, FONT_SIZE)
    board_x = MARGIN_WIDTH
    board_y = MARGIN_HEIGHT
    
    for row in range(8):
        for col in range(8):
            # Determine base color
            base_color = LIGHT_BROWN if (row + col) % 2 == 0 else DARK_BROWN
            if (row, col) == selected_pos:
                color = SELECTED_COLOR
            elif legal_moves and (row, col) in legal_moves:
                color = HIGHLIGHT_COLOR
            else:
                color = base_color
            
            pygame.draw.rect(win, color, (board_x + col * SQUARE_SIZE, 
                                         board_y + row * SQUARE_SIZE, 
                                         SQUARE_SIZE, SQUARE_SIZE))
    
    # Labels
    for i in range(8):
        label = font.render(str(8 - i), True, TEXT_COLOR)
        win.blit(label, (board_x - 30, board_y + i * SQUARE_SIZE + SQUARE_SIZE // 2))
        
        label = font.render(chr(65 + i), True, TEXT_COLOR)
        win.blit(label, (board_x + i * SQUARE_SIZE + SQUARE_SIZE // 2.5, 
                        board_y + BOARD_SIZE + 10))

def draw_pieces(win, pieces, selected_pos=None):
    board_x = MARGIN_WIDTH
    board_y = MARGIN_HEIGHT
    
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece != EMPTY and (row, col) != selected_pos:
                win.blit(pieces[piece], (board_x + col * SQUARE_SIZE, 
                                        board_y + row * SQUARE_SIZE))

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

def main():
    pygame.init()
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Chessboard")

    pieces = load_pieces()
    dragging = False
    selected_piece = None
    selected_pos = None
    dragged_piece_image = None
    mouse_offset = (0, 0)

    # Move log and scrollbar variables
    font = pygame.font.Font(None, 36)
    move_log = []
    scroll_offset = 0
    is_scrolling = False
    SCROLLBAR_WIDTH = 10
    MOVE_LOG_WIDTH = 200
    MOVE_LOG_HEIGHT = BOARD_SIZE
    LINE_HEIGHT = 30

    current_move_number = 1
    white_to_move = True

    legal_moves = []
    selected_pos = None

    running = True
    while running:
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                col = (mx - MARGIN_WIDTH) // SQUARE_SIZE
                row = (my - MARGIN_HEIGHT) // SQUARE_SIZE
                if 0 <= row < 8 and 0 <= col < 8 and board[row][col] != EMPTY:
                    selected_pos = (row, col)
                    legal_moves = get_legal_moves(board, selected_pos)
                    # Store original piece and position
                    selected_piece = board[row][col]
                    dragged_piece_image = pieces[selected_piece]
                    mouse_offset = (mx - (MARGIN_WIDTH + col * SQUARE_SIZE),
                                    my - (MARGIN_HEIGHT + row * SQUARE_SIZE))
                    dragging = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if dragging and selected_pos:
                    end_col = (mx - MARGIN_WIDTH) // SQUARE_SIZE
                    end_row = (my - MARGIN_HEIGHT) // SQUARE_SIZE
                    valid_move = False

                    if 0 <= end_row < 8 and 0 <= end_col < 8:
                        if (end_row, end_col) in legal_moves:
                            # Update board state
                            start_row, start_col = selected_pos
                            capture = board[end_row][end_col] != EMPTY
                            
                            # Play sound
                            if capture:
                                capture_sound.play()
                            else:
                                move_sound.play()

                            # Make the move
                            board[start_row][start_col] = EMPTY
                            board[end_row][end_col] = selected_piece

                            # Update move log
                            move_notation = print_move_notation(selected_piece, 
                                                              selected_pos, 
                                                              (end_row, end_col), 
                                                              capture)
                            
                            if white_to_move:
                                move_log.append(f"{current_move_number}. {move_notation}")
                            else:
                                if move_log:
                                    move_log[-1] += f" {move_notation}"
                                else:
                                    move_log.append(f"{current_move_number}. ... {move_notation}")
                                current_move_number += 1
                            
                            white_to_move = not white_to_move
                            valid_move = True

                    if not valid_move:
                        # Reset to original position
                        pass  # Board was never modified during drag

                    # Reset dragging state
                    dragging = False
                    selected_pos = None
                    legal_moves = []

                is_scrolling = False

            elif event.type == pygame.MOUSEMOTION:
                if is_scrolling:
                    # Calculate new scroll offset based on mouse position
                    total_content_height = len(move_log) * LINE_HEIGHT
                    scroll_offset = (my - MARGIN_HEIGHT) / MOVE_LOG_HEIGHT * total_content_height
                    scroll_offset = max(0, min(scroll_offset, total_content_height - MOVE_LOG_HEIGHT))

            elif event.type == pygame.MOUSEWHEEL:
                # Add mouse wheel scrolling support
                scroll_offset = max(0, scroll_offset - event.y * LINE_HEIGHT)

        # Update display
        win.fill(BACKGROUND_COLOR)
        draw_board(win)
        draw_pieces(win, pieces)

        win.fill(BACKGROUND_COLOR)
        draw_board(win, legal_moves, selected_pos)
        draw_pieces(win, pieces, selected_pos)
                # Draw move log area
        log_x = MARGIN_WIDTH + BOARD_SIZE + 20
        log_y = MARGIN_HEIGHT
        pygame.draw.rect(win, (50, 50, 50), (log_x, log_y, MOVE_LOG_WIDTH, MOVE_LOG_HEIGHT))

        # Calculate visible moves
        start_idx = int(scroll_offset // LINE_HEIGHT)
        end_idx = start_idx + (MOVE_LOG_HEIGHT // LINE_HEIGHT) + 1
        visible_moves = move_log[start_idx:end_idx]

        # Draw visible moves
        for i, move in enumerate(visible_moves):
            text = font.render(move, True, TEXT_COLOR)
            win.blit(text, (log_x + 5, log_y + i*LINE_HEIGHT - (scroll_offset % LINE_HEIGHT)))

        # Draw scrollbar if needed
        total_content_height = len(move_log) * LINE_HEIGHT
        if total_content_height > MOVE_LOG_HEIGHT:
            # Calculate scrollbar thumb proportions
            thumb_height = MOVE_LOG_HEIGHT * (MOVE_LOG_HEIGHT / total_content_height)
            thumb_position = (scroll_offset / total_content_height) * MOVE_LOG_HEIGHT
            pygame.draw.rect(win, (100, 100, 100), (
                log_x + MOVE_LOG_WIDTH - SCROLLBAR_WIDTH,
                log_y + thumb_position,
                SCROLLBAR_WIDTH,
                thumb_height
            ))
        # Draw dragged piece
        if dragging and selected_pos:
            piece_x = mx - mouse_offset[0]
            piece_y = my - mouse_offset[1]
            win.blit(dragged_piece_image, (piece_x, piece_y))


        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()