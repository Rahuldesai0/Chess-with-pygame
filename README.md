I am working on a chess pygame with an AI chess bot

Commit 1: 
1. Chess board setup with pieces
2. Using FEN notation for chess positions
3. Drag and dropping pieces
4. Chess move log with the standard chess move notation 
5. Sound Effects for normal move and capture

Commit 2:
1. Added all basic piece movements for all pieces
2. Highlight all the legal moves of the piece selected
3. Added special moves such as castling, en passant, promotion, check, checkmate
4. Added sound effects for check and checkmate

Commit 3:
1. Added turn based moves
2. Added captured pieces area and relative points
3. Added game ending conditions such as checkmate, stalemate and other types of draws

Commit 4:
1. Preventing castle during check or when intermediate square attacked
2. Put random move playing AI and main menu screen to choose which side is Player or AI
3. Put all AI code into separate file which will handle all the move selection logic