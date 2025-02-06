import pygame
import os
from util import *

# Global bonus variables for promotions.
bonus_white = 0
bonus_black = 0

def draw_board(win, legal_moves=None, selected_pos=None, in_check_pos=None):
    font = pygame.font.Font(None, FONT_SIZE)
    board_x = MARGIN_WIDTH
    board_y = MARGIN_HEIGHT

    for row in range(8):
        for col in range(8):
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

            # Draw check indicator
            if in_check_pos and (row, col) == in_check_pos:
                pygame.draw.rect(win, CHECK_COLOR, 
                                (board_x + col * SQUARE_SIZE,
                                 board_y + row * SQUARE_SIZE,
                                 SQUARE_SIZE, SQUARE_SIZE), 3)

    # Labels for rows and columns
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
                
def draw_promotion_menu(win, pieces, pos, color):
    row, col = pos
    menu_x = MARGIN_WIDTH + col * SQUARE_SIZE
    menu_y = MARGIN_HEIGHT + row * SQUARE_SIZE

    # Adjust position if near board edges
    if row <= 1:  # Near top
        menu_y += SQUARE_SIZE
    else:         # Near bottom
        menu_y -= SQUARE_SIZE * 4

    pygame.draw.rect(win, (200, 200, 200), 
                     (menu_x, menu_y, SQUARE_SIZE, SQUARE_SIZE * 4))

    for i, piece_type in enumerate(PROMOTION_PIECES):
        piece_code = color | piece_type
        win.blit(pieces[piece_code], (menu_x, menu_y + i * SQUARE_SIZE))

def draw_captured_and_points(win, captured_pieces, small_pieces):
    gap = 5                     # Gap between icons
    icon_size = CAPTURED_PIECE_SIZE  # Assumed defined in util.py
    font = pygame.font.Font(None, 30)

    # --- Top Half: Captured White Pieces (taken by Black) ---
    top_x = 10
    top_y = 10  # Starting near the top of the window.
    x = top_x
    row_num = 0
    for i, code in enumerate(captured_pieces['black']):
        if i % 4 == 0 and i != 0:
            row_num += 1
            x = top_x
        win.blit(small_pieces[code], (x, top_y + row_num * (icon_size + gap)))
        x += icon_size + gap

    # --- Bottom Half: Captured Black Pieces (taken by White) ---
    bottom_x = 10
    bottom_y = WINDOW_HEIGHT - (icon_size * 2) - 20
    x = bottom_x
    row_num = 0
    for i, code in enumerate(captured_pieces['white']):
        if i % 4 == 0 and i != 0:
            row_num += 1
            x = bottom_x
        win.blit(small_pieces[code], (x, bottom_y - row_num * (icon_size + gap)))
        x += icon_size + gap

    # --- Points Difference ---
    # Incorporate bonus points from promotions.
    white_points = sum(PIECE_VALUES[pc & 7] for pc in captured_pieces['white']) + bonus_white
    black_points = sum(PIECE_VALUES[pc & 7] for pc in captured_pieces['black']) + bonus_black

    if white_points > black_points:
        diff = white_points - black_points
        diff_text = font.render(f"+{diff}", True, TEXT_COLOR)
        win.blit(diff_text, (bottom_x + 200, bottom_y + icon_size))
    elif black_points > white_points:
        diff = black_points - white_points
        diff_text = font.render(f"+{diff}", True, TEXT_COLOR)
        win.blit(diff_text, (top_x + 200, top_y + icon_size))
    # If equal, nothing is drawn.

def is_insufficient_material():
    white_pieces = []
    black_pieces = []
    pawn_rook_queen = {PAWN, ROOK, QUEEN}
    for row in board:
        for piece in row:
            if piece == EMPTY:
                continue
            piece_type = piece & 7
            color = piece & 24
            if piece_type in pawn_rook_queen:
                return False  # These pieces can force checkmate
            if color == WHITE:
                white_pieces.append(piece_type)
            else:
                black_pieces.append(piece_type)
    
    # Check for King vs King
    if len(white_pieces) == 1 and len(black_pieces) == 1:
        return True
    
    # Check for King and Knight vs King
    if (len(white_pieces) == 2 and white_pieces.count(KNIGHT) == 1 and len(black_pieces) == 1) or \
       (len(black_pieces) == 2 and black_pieces.count(KNIGHT) == 1 and len(white_pieces) == 1):
        return True
    
    # Check for King and Bishop vs King
    if (len(white_pieces) == 2 and white_pieces.count(BISHOP) == 1 and len(black_pieces) == 1) or \
       (len(black_pieces) == 2 and black_pieces.count(BISHOP) == 1 and len(white_pieces) == 1):
        return True
    
    # Check for all bishops on the same color
    bishop_positions = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece != EMPTY and (piece & 7) == BISHOP:
                bishop_positions.append((r, c))
    
    if len(bishop_positions) <= 1:
        pass
    else:
        first_color = (bishop_positions[0][0] + bishop_positions[0][1]) % 2
        all_same = all((r + c) % 2 == first_color for (r, c) in bishop_positions)
        if all_same:
            white_non_bishops = [p for p in white_pieces if p not in (KING, BISHOP)]
            black_non_bishops = [p for p in black_pieces if p not in (KING, BISHOP)]
            if not white_non_bishops and not black_non_bishops:
                return True
    
    return False

def main():
    global bonus_white, bonus_black

    pygame.init()
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Chessboard")

    pieces, small_pieces = load_pieces()
    dragging = False
    selected_piece = None
    selected_pos = None
    dragged_piece_image = None
    mouse_offset = (0, 0)
    moved_positions = set()
    en_passant_target = None

    promotion_pending = False
    promotion_pos = None
    promotion_color = WHITE

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
    captured_pieces = {'white': [], 'black': []}

    legal_moves = []
    selected_pos = None

    game_over = False
    position_history = []

    running = True
    while running:
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            # Always allow quit events even if game is over.
            if event.type == pygame.QUIT:
                running = False
                continue

            # If the game is over, ignore any further move input.
            if game_over and event.type not in (pygame.QUIT,):
                continue

            # --- Promotion Event Handling (Modified) ---
            if promotion_pending:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    p_row, p_col = promotion_pos
                    menu_x = MARGIN_WIDTH + p_col * SQUARE_SIZE
                    menu_y = MARGIN_HEIGHT + p_row * SQUARE_SIZE
                    if p_row <= 1:
                        menu_y += SQUARE_SIZE
                    else:
                        menu_y -= SQUARE_SIZE * 4
                    if (menu_x <= mx < menu_x + SQUARE_SIZE and
                        menu_y <= my < menu_y + SQUARE_SIZE * 4):
                        index = (my - menu_y) // SQUARE_SIZE
                        if 0 <= index < 4:
                            new_piece = promotion_color | PROMOTION_PIECES[index]
                            # Award the opponent a pawn.
                            if promotion_color == WHITE:
                                captured_pieces['black'].append(WHITE | PAWN)
                            else:
                                captured_pieces['white'].append(BLACK | PAWN)
                            board[promotion_pos[0]][promotion_pos[1]] = new_piece
                            if promotion_color == WHITE:
                                bonus_white += PIECE_VALUES[new_piece & 7]
                            else:
                                bonus_black += PIECE_VALUES[new_piece & 7]
                            if move_log:
                                last_move = move_log[-1]
                                if '=' not in last_move:
                                    move_log[-1] += f"={PROMOTION_CODES[PROMOTION_PIECES[index]]}"
                            promotion_pending = False
                            move_sound.play()
                            current_fen = generate_fen(en_passant_target)
                            fen_part = ' '.join(current_fen.split()[:4])
                            position_history.append(fen_part)
                            if position_history.count(fen_part) >= 3:
                                # Append the threefold repetition message at the end.
                                move_log.append("Draw by three-fold repetition")
                                game_over = True
                            if is_insufficient_material():
                                move_log.append("Draw by insufficient material")
                                game_over = True

            else:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    col = (mx - MARGIN_WIDTH) // SQUARE_SIZE
                    row = (my - MARGIN_HEIGHT) // SQUARE_SIZE
                    if 0 <= row < 8 and 0 <= col < 8:
                        piece = board[row][col]
                        if piece != EMPTY:
                            piece_color = piece & 24  # Extract color from the piece
                            if (white_to_move and piece_color == WHITE) or (not white_to_move and piece_color == BLACK):
                                selected_pos = (row, col)
                                legal_moves = get_legal_moves(board, selected_pos, moved_positions, en_passant_target)
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
                                start_row, start_col = selected_pos
                                capture = board[end_row][end_col] != EMPTY
                                is_en_passant = False
                                captured_piece_code = None
                                if (selected_piece & 7) == PAWN and (end_row, end_col) == en_passant_target:
                                    direction = -1 if (selected_piece & 24) == WHITE else 1
                                    captured_pawn_row = end_row - direction
                                    if 0 <= captured_pawn_row < 8:
                                        captured_piece_code = board[captured_pawn_row][end_col]
                                        board[captured_pawn_row][end_col] = EMPTY
                                        is_en_passant = True
                                        capture = True
                                else:
                                    if capture:
                                        captured_piece_code = board[end_row][end_col]
                                board[start_row][start_col] = EMPTY
                                board[end_row][end_col] = selected_piece
                                if capture:
                                    capture_sound.play()
                                    if white_to_move:
                                        captured_pieces['white'].append(captured_piece_code)
                                    else:
                                        captured_pieces['black'].append(captured_piece_code)
                                else:
                                    move_sound.play()
                                # Save move notation for later logging.
                                move_notation = print_move_notation(selected_piece, selected_pos, (end_row, end_col), capture)

                                original_white_to_move = white_to_move
                                white_to_move = not white_to_move
                                current_color = WHITE if white_to_move else BLACK

                                # Perform castling if necessary.
                                if (selected_piece & 7) == KING and abs(end_col - start_col) == 2:
                                    rook_from, rook_to = CASTLING_ROOK_MOVES[(start_row, start_col)][(end_row, end_col)]
                                    board[rook_to[0]][rook_to[1]] = board[rook_from[0]][rook_from[1]]
                                    board[rook_from[0]][rook_from[1]] = EMPTY
                                    moved_positions.add(rook_from)

                                # Set en passant target if applicable.
                                if (selected_piece & 7) == PAWN and abs(start_row - end_row) == 2:
                                    direction = -1 if (selected_piece & 24) == WHITE else 1
                                    en_passant_target = (start_row + direction, start_col)
                                else:
                                    en_passant_target = None

                                # Check for promotion.
                                if (selected_piece & 7) == PAWN:
                                    color = selected_piece & 24
                                    if (color == WHITE and end_row == 0) or (color == BLACK and end_row == 7):
                                        promotion_pending = True
                                        promotion_pos = (end_row, end_col)
                                        promotion_color = color

                                moved_positions.add((start_row, start_col))
                                valid_move = True

                                # First, add the move notation.
                                if original_white_to_move:
                                    move_log.append(f"{current_move_number}. {move_notation}")
                                else:
                                    if move_log:
                                        move_log[-1] += f" {move_notation}"
                                        current_move_number += 1
                                    else:
                                        move_log.append(f"{current_move_number}. ... {move_notation}")
                                        current_move_number += 1

                                # Now check for game-ending conditions.
                                has_legal_moves = False
                                for r in range(8):
                                    for c in range(8):
                                        piece = board[r][c]
                                        if piece != EMPTY and (piece & 24) == current_color:
                                            if get_legal_moves(board, (r, c), moved_positions, en_passant_target):
                                                has_legal_moves = True
                                                break
                                    if has_legal_moves:
                                        break
                                if not has_legal_moves:
                                    in_check = is_in_check(board, current_color, moved_positions, en_passant_target)
                                    if in_check:
                                        winner = "White" if current_color == BLACK else "Black"
                                        # Append the win message after the move notation.
                                        move_log.append(f"{winner} won by checkmate")
                                        game_over = True
                                        checkmate_sound.play()
                                    else:
                                        move_log.append("Draw by stalemate")
                                        game_over = True
                                elif is_insufficient_material():
                                    move_log.append("Draw by insufficient material")
                                    game_over = True
                                else:
                                    current_fen = generate_fen(en_passant_target)
                                    fen_part = ' '.join(current_fen.split()[:4])
                                    position_history.append(fen_part)
                                    if position_history.count(fen_part) >= 3:
                                        move_log.append("Draw by three-fold repetition")
                                        game_over = True

                        dragging = False
                        selected_pos = None
                        legal_moves = []
                    is_scrolling = False

                elif event.type == pygame.MOUSEMOTION:
                    if is_scrolling:
                        total_content_height = len(move_log) * LINE_HEIGHT
                        scroll_offset = (my - MARGIN_HEIGHT) / MOVE_LOG_HEIGHT * total_content_height
                        scroll_offset = max(0, min(scroll_offset, total_content_height - MOVE_LOG_HEIGHT))
                elif event.type == pygame.MOUSEWHEEL:
                    scroll_offset = max(0, scroll_offset - event.y * LINE_HEIGHT)

        # Drawing phase
        win.fill(BACKGROUND_COLOR)
        draw_board(win, legal_moves, selected_pos)
        draw_pieces(win, pieces, selected_pos)
        draw_captured_and_points(win, captured_pieces, small_pieces)

        # Draw move log (positioned to the right of the board)
        log_x = MARGIN_WIDTH + BOARD_SIZE + 20
        log_y = MARGIN_HEIGHT
        pygame.draw.rect(win, (50, 50, 50), (log_x, log_y, MOVE_LOG_WIDTH, MOVE_LOG_HEIGHT))
        start_idx = int(scroll_offset // LINE_HEIGHT)
        end_idx = start_idx + (MOVE_LOG_HEIGHT // LINE_HEIGHT) + 1
        visible_moves = move_log[start_idx:end_idx]
        for i, move in enumerate(visible_moves):
            text = font.render(move, True, TEXT_COLOR)
            win.blit(text, (log_x + 5, log_y + i * LINE_HEIGHT - (scroll_offset % LINE_HEIGHT)))
        total_content_height = len(move_log) * LINE_HEIGHT
        if total_content_height > MOVE_LOG_HEIGHT:
            thumb_height = MOVE_LOG_HEIGHT * (MOVE_LOG_HEIGHT / total_content_height)
            thumb_position = (scroll_offset / total_content_height) * MOVE_LOG_HEIGHT
            pygame.draw.rect(win, (100, 100, 100), (
                log_x + MOVE_LOG_WIDTH - SCROLLBAR_WIDTH,
                log_y + thumb_position,
                SCROLLBAR_WIDTH,
                thumb_height
            ))
        if promotion_pending:
            draw_promotion_menu(win, pieces, promotion_pos, promotion_color)
        if dragging and selected_pos:
            piece_x = mx - mouse_offset[0]
            piece_y = my - mouse_offset[1]
            win.blit(dragged_piece_image, (piece_x, piece_y))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
