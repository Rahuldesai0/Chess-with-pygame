import pygame
import os
import sys
import random
from util import *
from chess_ai import get_ai_move

# Global bonus variables for promotions.
bonus_white = 0
bonus_black = 0

#############################################
#         HELPER FUNCTIONS                #
#############################################

def add_check_symbols(move_notation, board, moved_positions, en_passant_target, opponent_color):
    """
    Returns the move notation string appended with '+' if the move gives check
    and with '#' if it gives checkmate.
    """
    if is_in_check(board, opponent_color, moved_positions, en_passant_target):
        has_moves = False
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if p != EMPTY and (p & 24) == opponent_color:
                    if get_legal_moves(board, (r, c), moved_positions, en_passant_target):
                        has_moves = True
                        break
            if has_moves:
                break
        if has_moves:
            return move_notation + "+"
        else:
            return move_notation + "#"
    return move_notation

def get_castling_rights(board, moved_positions):
    rights = ""
    # White castling rights.
    if (7, 4) not in moved_positions and board[7][4] == (WHITE | KING):
         if (7, 7) not in moved_positions and board[7][7] == (WHITE | ROOK):
              rights += "K"
         if (7, 0) not in moved_positions and board[7][0] == (WHITE | ROOK):
              rights += "Q"
    # Black castling rights.
    if (0, 4) not in moved_positions and board[0][4] == (BLACK | KING):
         if (0, 7) not in moved_positions and board[0][7] == (BLACK | ROOK):
              rights += "k"
         if (0, 0) not in moved_positions and board[0][0] == (BLACK | ROOK):
              rights += "q"
    return rights if rights != "" else "-"

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

#############################################
#         MENU & AI MOVE FUNCTIONS        #
#############################################

def draw_menu(win, font, buttons):
    """Draws the menu with a list of button tuples (text, rect)."""
    win.fill((0, 0, 0))  # Black background
    for btn_text, btn_rect in buttons:
        pygame.draw.rect(win, (200, 200, 200), btn_rect)
        text_surf = font.render(btn_text, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=btn_rect.center)
        win.blit(text_surf, text_rect)

def menu_loop(win):
    """Loops until a menu button is clicked and returns a mode code."""
    menu_font = pygame.font.Font(None, 36)
    button_width = 300
    button_height = 50
    gap = 20
    start_y = (WINDOW_HEIGHT - (4 * button_height + 3 * gap)) // 2
    buttons = []
    modes = ["Player vs Player", "White vs AI", "Black vs AI", "AI vs AI"]
    for i, mode in enumerate(modes):
        rect = pygame.Rect((WINDOW_WIDTH - button_width) // 2,
                           start_y + i*(button_height+gap),
                           button_width, button_height)
        buttons.append((mode, rect))
    selected_mode = None
    while selected_mode is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for mode_text, rect in buttons:
                    if rect.collidepoint(mx, my):
                        selected_mode = mode_text
        draw_menu(win, menu_font, buttons)
        pygame.display.flip()
    # Map the selected mode to a simpler code:
    if selected_mode == "Player vs Player":
        return "pvp"
    elif selected_mode == "White vs AI":
        return "white_vs_ai"
    elif selected_mode == "Black vs AI":
        return "black_vs_ai"
    elif selected_mode == "AI vs AI":
        return "ai_vs_ai"
    
def ai_move_function(color, board, moved_positions, en_passant_target,
                     captured_pieces, move_log, position_history, current_move_number, white_to_move):
    """
    This function converts the current state into a FEN string,
    calls get_ai_move(fen) from your separate AI module to decide on a move,
    then applies that move (handling en passant, castling, random promotion, etc.),
    plays appropriate sound effects (for move, capture, check, or checkmate),
    updates captured pieces, move log, and FEN history (for three‑fold repetition),
    and returns the updated game state.
    """
    # 1. Convert the current state to a FEN string.
    active_color = "w" if white_to_move else "b"
    castling_rights = get_castling_rights(board, moved_positions)
    current_fen = generate_fen(board, active_color, castling_rights, en_passant_target, halfmove=0, fullmove=1)
    
    # 2. Get the AI move from the external module.
    best_move = get_ai_move(current_fen)
    if best_move is None:
        # No legal moves available.
        return board, moved_positions, en_passant_target, captured_pieces, move_log, position_history, current_move_number, True

    # Unpack the move.
    start, end = best_move
    piece = board[start[0]][start[1]]
    capture = board[end[0]][end[1]] != EMPTY
    captured_piece_code = None
    start_row, start_col = start
    end_row, end_col = end
    
    # 3. En passant check.
    if (piece & 7) == PAWN and (end_row, end_col) == en_passant_target:
        direction = -1 if (piece & 24) == WHITE else 1
        captured_pawn_row = end_row - direction
        captured_piece_code = board[captured_pawn_row][end_col]
        board[captured_pawn_row][end_col] = EMPTY
        capture = True
    else:
        if capture:
            captured_piece_code = board[end_row][end_col]
            
    # 4. Apply the move.
    board[start_row][start_col] = EMPTY
    board[end_row][end_col] = piece

    # 5. Castling check.
    if (piece & 7) == KING and abs(end_col - start_col) == 2:
        rook_from, rook_to = CASTLING_ROOK_MOVES[(start_row, start_col)][(end_row, end_col)]
        board[rook_to[0]][rook_to[1]] = board[rook_from[0]][rook_from[1]]
        board[rook_from[0]][rook_from[1]] = EMPTY
        moved_positions.add(rook_from)

    # 6. Update en passant target.
    if (piece & 7) == PAWN and abs(start_row - end_row) == 2:
        direction = -1 if (piece & 24) == WHITE else 1
        en_passant_target = (start_row + direction, start_col)
    else:
        en_passant_target = None

    # 7. Promotion check: choose a random promotion piece.
    if (piece & 7) == PAWN:
        color_piece = piece & 24
        if (color_piece == WHITE and end_row == 0) or (color_piece == BLACK and end_row == 7):
            promoted_piece_type = random.choice(PROMOTION_PIECES)
            new_piece = color_piece | promoted_piece_type
            board[end_row][end_col] = new_piece
            if color_piece == WHITE:
                captured_pieces['black'].append(WHITE | PAWN)
                global bonus_white, bonus_black
                bonus_white += PIECE_VALUES[new_piece & 7]
            else:
                captured_pieces['white'].append(BLACK | PAWN)
                bonus_black += PIECE_VALUES[new_piece & 7]

    # 8. Record captured piece if a capture occurred.
    if capture and captured_piece_code is not None:
        if color == WHITE:
            captured_pieces['white'].append(captured_piece_code)
        else:
            captured_pieces['black'].append(captured_piece_code)

    moved_positions.add((start_row, start_col))
    
    # 9. Play sound effects.
    if capture:
        capture_sound.play()
    else:
        move_sound.play()
    
    # 10. Create move notation (including check or checkmate symbols).
    move_notation = print_move_notation(piece, start, end, capture)
    opponent_color = BLACK if color == WHITE else WHITE
    move_notation = add_check_symbols(move_notation, board, moved_positions, en_passant_target, opponent_color)
    
    if color == WHITE:
        move_log.append(f"{current_move_number}. {move_notation}")
    else:
        if move_log:
            move_log[-1] += f" {move_notation}"
        else:
            move_log.append(f"{current_move_number}. ... {move_notation}")
        current_move_number += 1
    
    # 11. Check for game termination conditions.
    # First, check for insufficient material.
    if is_insufficient_material():
        move_log.append("Draw by insufficient material")
        game_over = True
    else:
        has_legal_moves = False
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if p != EMPTY and (p & 24) == opponent_color:
                    if get_legal_moves(board, (r, c), moved_positions, en_passant_target):
                        has_legal_moves = True
                        break
            if has_legal_moves:
                break

        if not has_legal_moves:
            in_check = is_in_check(board, opponent_color, moved_positions, en_passant_target)
            if in_check:
                winner = "White" if opponent_color == BLACK else "Black"
                move_log.append(f"{winner} won by checkmate")
                checkmate_sound.play()
            else:
                move_log.append("Draw by stalemate")
            game_over = True
        else:
            # If the move gives check (but not mate), play the check sound.
            if is_in_check(board, opponent_color, moved_positions, en_passant_target):
                check_sound.play()
            active_color = "w" if white_to_move else "b"
            castling_rights = get_castling_rights(board, moved_positions)
            current_fen = generate_fen(board, active_color, castling_rights, en_passant_target, halfmove=0, fullmove=1)
            fen_part = ' '.join(current_fen.split()[:4])
            position_history.append(fen_part)
            if position_history.count(fen_part) >= 3:
                move_log.append("Draw by three-fold repetition")
                game_over = True
            else:
                game_over = False  # Explicitly set game_over to False if no termination condition was met.

    return board, moved_positions, en_passant_target, captured_pieces, move_log, position_history, current_move_number, game_over


#############################################
#         GAME DRAWING FUNCTIONS          #
#############################################

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

            # Draw check indicator.
            if in_check_pos and (row, col) == in_check_pos:
                pygame.draw.rect(win, CHECK_COLOR,
                                (board_x + col * SQUARE_SIZE,
                                 board_y + row * SQUARE_SIZE,
                                 SQUARE_SIZE, SQUARE_SIZE), 3)

    # Draw row and column labels.
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

    if row <= 1:
        menu_y += SQUARE_SIZE
    else:
        menu_y -= SQUARE_SIZE * 4

    pygame.draw.rect(win, (200, 200, 200),
                     (menu_x, menu_y, SQUARE_SIZE, SQUARE_SIZE * 4))

    for i, piece_type in enumerate(PROMOTION_PIECES):
        piece_code = color | piece_type
        win.blit(pieces[piece_code], (menu_x, menu_y + i * SQUARE_SIZE))

def draw_captured_and_points(win, captured_pieces, small_pieces):
    gap = 5
    icon_size = CAPTURED_PIECE_SIZE
    font = pygame.font.Font(None, 30)

    # Draw captured white pieces (taken by Black).
    top_x = 10
    top_y = 10
    x = top_x
    row_num = 0
    for i, code in enumerate(captured_pieces['black']):
        if i % 4 == 0 and i != 0:
            row_num += 1
            x = top_x
        win.blit(small_pieces[code], (x, top_y + row_num * (icon_size + gap)))
        x += icon_size + gap

    # Draw captured black pieces (taken by White).
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

    # Draw points difference.
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
                return False
            if color == WHITE:
                white_pieces.append(piece_type)
            else:
                black_pieces.append(piece_type)

    if len(white_pieces) == 1 and len(black_pieces) == 1:
        return True

    if (len(white_pieces) == 2 and white_pieces.count(KNIGHT) == 1 and len(black_pieces) == 1) or \
       (len(black_pieces) == 2 and black_pieces.count(KNIGHT) == 1 and len(white_pieces) == 1):
        return True

    if (len(white_pieces) == 2 and white_pieces.count(BISHOP) == 1 and len(black_pieces) == 1) or \
       (len(black_pieces) == 2 and black_pieces.count(BISHOP) == 1 and len(white_pieces) == 1):
        return True

    bishop_positions = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece != EMPTY and (piece & 7) == BISHOP:
                bishop_positions.append((r, c))

    if len(bishop_positions) > 1:
        first_color = (bishop_positions[0][0] + bishop_positions[0][1]) % 2
        all_same = all((r + c) % 2 == first_color for (r, c) in bishop_positions)
        if all_same:
            white_non_bishops = [p for p in white_pieces if p not in (KING, BISHOP)]
            black_non_bishops = [p for p in black_pieces if p not in (KING, BISHOP)]
            if not white_non_bishops and not black_non_bishops:
                return True
    return False

#############################################
#                 MAIN GAME               #
#############################################

def main():
    global bonus_white, bonus_black, board

    pygame.init()
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Chessboard")

    pieces, small_pieces = load_pieces()
    # Initialize board from starting FEN.
    load_board_from_fen(starting_fen)

    # Show menu and get game mode.
    game_mode = menu_loop(win)
    # game_mode is one of: "pvp", "white_vs_ai", "black_vs_ai", "ai_vs_ai"

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
    clock = pygame.time.Clock()

    # Main game loop:
    while True:
        clock.tick(30)  # Limit FPS to 30.
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # If game is over, ignore further move input.
            if game_over:
                continue

            # --- Promotion handling (for human moves) ---
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
                            active_color = "w" if white_to_move else "b"
                            castling_rights = get_castling_rights(board, moved_positions)
                            current_fen = generate_fen(board, active_color, castling_rights, en_passant_target)
                            fen_part = ' '.join(current_fen.split()[:4])
                            position_history.append(fen_part)
                            if position_history.count(fen_part) >= 3:
                                move_log.append("Draw by three-fold repetition")
                                game_over = True

                            if is_insufficient_material():
                                move_log.append("Draw by insufficient material")
                                game_over = True
                continue

            # --- Human move handling (only if it is this side’s turn) ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                col = (mx - MARGIN_WIDTH) // SQUARE_SIZE
                row = (my - MARGIN_HEIGHT) // SQUARE_SIZE
                if 0 <= row < 8 and 0 <= col < 8:
                    piece = board[row][col]
                    if piece != EMPTY:
                        piece_color = piece & 24
                        # Determine if we should allow input based on game mode.
                        if game_mode == "pvp":
                            # In PvP, allow input if the piece color matches the turn.
                            if (white_to_move and piece_color != WHITE) or (not white_to_move and piece_color != BLACK):
                                continue
                        elif game_mode == "white_vs_ai":
                            # In white_vs_ai, human controls White. So only allow input if it's White's turn.
                            if not (white_to_move and piece_color == WHITE):
                                continue
                        elif game_mode == "black_vs_ai":
                            # In black_vs_ai, human controls Black. So only allow input if it's Black's turn.
                            if not ((not white_to_move) and piece_color == BLACK):
                                continue
                        elif game_mode == "ai_vs_ai":
                            # No human input if AI plays both sides.
                            continue

                        # If we passed the conditions, process the input:
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
                    if 0 <= end_row < 8 and 0 <= end_col < 8:
                        if (end_row, end_col) in legal_moves:
                            start_row, start_col = selected_pos
                            capture = board[end_row][end_col] != EMPTY
                            is_en_passant = False
                            captured_piece_code = None
                            if (selected_piece & 7) == PAWN and (end_row, end_col) == en_passant_target:
                                direction = -1 if (selected_piece & 24) == WHITE else 1
                                captured_pawn_row = end_row - direction
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
                            move_notation = print_move_notation(selected_piece, selected_pos, (end_row, end_col), capture)
                            original_white_to_move = white_to_move
                            white_to_move = not white_to_move
                            opponent_color = WHITE if white_to_move else BLACK
                            move_notation = add_check_symbols(move_notation, board, moved_positions, en_passant_target, opponent_color)
                            if (selected_piece & 7) == KING and abs(end_col - start_col) == 2:
                                rook_from, rook_to = CASTLING_ROOK_MOVES[(start_row, start_col)][(end_row, end_col)]
                                board[rook_to[0]][rook_to[1]] = board[rook_from[0]][rook_from[1]]
                                board[rook_from[0]][rook_from[1]] = EMPTY
                                moved_positions.add(rook_from)
                            if (selected_piece & 7) == PAWN and abs(start_row - end_row) == 2:
                                direction = -1 if (selected_piece & 24) == WHITE else 1
                                en_passant_target = (start_row + direction, start_col)
                            else:
                                en_passant_target = None
                            if (selected_piece & 7) == PAWN:
                                color_piece = selected_piece & 24
                                if (color_piece == WHITE and end_row == 0) or (color_piece == BLACK and end_row == 7):
                                    promotion_pending = True
                                    promotion_pos = (end_row, end_col)
                                    promotion_color = color_piece
                            moved_positions.add((start_row, start_col))
                            if original_white_to_move:
                                move_log.append(f"{current_move_number}. {move_notation}")
                            else:
                                if move_log:
                                    move_log[-1] += f" {move_notation}"
                                    current_move_number += 1
                                else:
                                    move_log.append(f"{current_move_number}. ... {move_notation}")
                                    current_move_number += 1

                            has_legal_moves = False
                            current_color = WHITE if white_to_move else BLACK
                            for r in range(8):
                                for c in range(8):
                                    p = board[r][c]
                                    if p != EMPTY and (p & 24) == current_color:
                                        if get_legal_moves(board, (r, c), moved_positions, en_passant_target):
                                            has_legal_moves = True
                                            break
                                if has_legal_moves:
                                    break
                            if not has_legal_moves:
                                in_check = is_in_check(board, current_color, moved_positions, en_passant_target)
                                if in_check:
                                    winner = "White" if current_color == BLACK else "Black"
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
                                active_color = "w" if white_to_move else "b"
                                castling_rights = get_castling_rights(board, moved_positions)
                                current_fen = generate_fen(board, active_color, castling_rights, en_passant_target)
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

        # --- AI move handling based on game mode ---
        if not game_over and not promotion_pending:
            current_color = WHITE if white_to_move else BLACK
            if game_mode == "pvp":
                pass  # both sides are human.
            elif game_mode == "white_vs_ai":
                # In white_vs_ai, white is human; black is AI.
                if not white_to_move:
                    pygame.time.delay(500)  # Artificial delay for AI "thinking"
                    board, moved_positions, en_passant_target, captured_pieces, move_log, position_history, current_move_number, game_over = \
                        ai_move_function(BLACK, board, moved_positions, en_passant_target,
                                         captured_pieces, move_log, position_history, current_move_number, white_to_move)
                    white_to_move = not white_to_move
            elif game_mode == "black_vs_ai":
                # In black_vs_ai, black is human; white is AI.
                if white_to_move:
                    pygame.time.delay(500)
                    board, moved_positions, en_passant_target, captured_pieces, move_log, position_history, current_move_number, game_over = \
                        ai_move_function(WHITE, board, moved_positions, en_passant_target,
                                         captured_pieces, move_log, position_history, current_move_number, white_to_move)
                    white_to_move = not white_to_move
            elif game_mode == "ai_vs_ai":
                pygame.time.delay(500)
                board, moved_positions, en_passant_target, captured_pieces, move_log, position_history, current_move_number, game_over = \
                    ai_move_function(current_color, board, moved_positions, en_passant_target,
                                     captured_pieces, move_log, position_history, current_move_number, white_to_move)
                white_to_move = not white_to_move

        # --- Drawing Phase ---
        win.fill(BACKGROUND_COLOR)
        draw_board(win, legal_moves, selected_pos)
        draw_pieces(win, pieces, selected_pos)
        draw_captured_and_points(win, captured_pieces, small_pieces)

        # Draw move log (to the right of the board)
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
