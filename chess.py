import pygame
import os
from util import *

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