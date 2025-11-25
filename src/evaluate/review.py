# uses: python-chess

def get_development(board):
def get_tension(board):
def get_control(board):
def get_mobility(board):
def is_center_controlled(board):
def king_safety(board):               # optional
def mobility_white(board):
def mobility_black(board)

def get_development(board: chess.Board):
    white_dev = 0
    black_dev = 0

    for square in [chess.A1, chess.H1]:
        if str(board.piece_at(square)) != 'R':
            white_dev += 1

    for square in [chess.B1, chess.G1]:
        if str(board.piece_at(square)) != 'N':
            white_dev += 1

    for square in [chess.C1, chess.F1]:
        if str(board.piece_at(square)) != 'B':
            white_dev += 1

    if str(board.piece_at(chess.D1)) != 'Q':
        white_dev += 1

    for square in [chess.A8, chess.H8]:
        if str(board.piece_at(square)) != 'r':
            black_dev += 1

    for square in [chess.B8, chess.G8]:
        if str(board.piece_at(square)) != 'n':
            black_dev += 1

    for square in [chess.C8, chess.F8]:
        if str(board.piece_at(square)) != 'b':
            black_dev += 1

    if str(board.piece_at(chess.D8)) != 'q':
        black_dev += 1

    return white_dev, black_dev

def get_tension(board):
    player_tension = sum(1 for move in board.legal_moves if board.is_capture(move))
    board.push(chess.Move.null())  # Make a null move to switch turns
    opponent_tension = sum(1 for move in board.legal_moves if board.is_capture(move))
    board.pop()  # Undo the null move

    if board.turn == True:
        return player_tension, opponent_tension
    else:
        return opponent_tension, player_tension

def get_mobility(board):
    player_mobility = sum(1 for move in board.legal_moves if str(board.piece_at(move.from_square)).lower() != 'p')
    board.push(chess.Move.null())  # Make a null move to switch turns
    opponent_mobility = sum(1 for move in board.legal_moves if str(board.piece_at(move.from_square)).lower() != 'p')
    board.pop()  # Undo the null move

    if board.turn == True:
        return player_mobility, opponent_mobility  # white, black
    else:
        return opponent_mobility, player_mobility  # white, black

def get_control(board: chess.Board):
    white_control = 0
    black_control = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            if piece.color == True:
                white_control += len(board.attacks(square))
            else:
                black_control += len(board.attacks(square))

    return white_control, black_control

def is_possible_sacrifice(board: chess.Board, move):

    if str(board.piece_at(move.from_square)).lower() == 'p':
        return False

    if board.is_capture(move):
        defending_squares = is_defended(board, move.to_square, by_color=not board.turn, return_list_of_defenders=True)

        if len(defending_squares) > 0:
            
            if board.piece_type_at(move.to_square) < board.piece_type_at(move.from_square):
                
                if (board.piece_type_at(move.to_square) != 2) or (board.piece_type_at(move.from_square) != 3):
                    for defending_square in defending_squares:
                        if board.piece_type_at(defending_square) < board.piece_type_at(move.from_square):
                            return True
                        else:
                            return False
                else:
                    return False
            else:
                return False             
        else:
            return False
        
    else:
        attackers = list(board.attackers(not board.turn, move.to_square))
        if len(attackers) > 0:
            for attacking_square in attackers:
                if is_defended(board, move.to_square, by_color=board.turn):
                    if board.piece_type_at(attacking_square) < board.piece_type_at(move.from_square):
                        if (board.piece_type_at(attacking_square) != 2) or (board.piece_type_at(move.from_square) != 3):
                            if not board.is_pinned(not board.turn, attacking_square):
                                return True
                else:
                    return True
        
        return False

def move_attacks_piece(board: chess.Board, move: chess.Move, return_attacked_piece=False):

    position_after_move = board.copy()
    position_after_move.push(move)
    
    if is_defended(position_after_move, move.to_square) or not board.is_attacked_by(position_after_move.turn, move.to_square):
        attacked_squares = list(position_after_move.attacks(move.to_square))
        for attacked_square in attacked_squares:
            if position_after_move.piece_at(attacked_square) is not None:
                if str(position_after_move.piece_at(attacked_square)).lower() != 'k':
                    if position_after_move.piece_at(attacked_square).color != position_after_move.piece_at(move.to_square).color:
                        if position_after_move.piece_type_at(attacked_square) > position_after_move.piece_type_at(move.to_square):
                            
                            if return_attacked_piece:
                                return position_after_move.piece_at(attacked_square)
                            return True
                        elif is_hanging(position_after_move, attacked_square, capturable_by=not position_after_move.turn):
                            if return_attacked_piece:
                                return position_after_move.piece_at(attacked_square)
                            return True
    
    return False