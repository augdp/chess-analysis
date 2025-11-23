import chess
import chess.engine
import chess.pgn


def game_outcome(game):
    losses = [
        "checkmated",
        "timeout",
        "abandoned",
        "resigned"
    ]
    player_color = game.metadata['player_color']
    if game.metadata[player_color]['result'] == 'win':
        return "win"
    elif game.metadata[player_color]['result'] in losses:
        return "loss"
    return "draw"


def play_moves(game, num_moves):
    """
    Create a board position after playing num_moves full moves from a game.
    
    Args:
        game: chess.pgn.Game object
        num_moves: Number of full moves to play (1 move = white + black)
    
    Returns:
        chess.Board object at the position after num_moves
    """
    board = game.board()
    moves = list(game.mainline_moves())
    
    # Calculate how many half-moves to play
    # num_moves full moves = num_moves * 2 half-moves
    half_moves_to_play = min(num_moves, len(moves))
    
    # Play the moves
    for move in moves[:half_moves_to_play]:
        board.push(move)
    
    return board


def position(board, engine, depth=20, time_limit=None):
    """
    Evaluate a chess position using Stockfish.
    
    Args:
        board: chess.Board object representing the position to evaluate
        engine: chess.engine.SimpleEngine object (Stockfish)
        depth: Search depth for the engine (default: 20)
        time_limit: Time limit in seconds for the analysis (default: 0.1s)
    
    Returns:
        int: Evaluation in centipawns from White's perspective
             Positive = White is better, Negative = Black is better
             Returns None if mate is found (we'll handle mate separately if needed)
    """

    if not time_limit:
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
    else:
        info = engine.analyse(board, chess.engine.Limit(depth=depth, time=time_limit))
    
    # Get the evaluation score
    score = info['score'].white()
    
    # Check if it's a mate score or centipawn score
    if score.is_mate() and score.mate() > 0:
        # Mate in N moves - we'll return a large value
        # Mate scores: positive if White mates, negative if Black mates
        mate_in = score.mate()
        if mate_in > 0:
            return 10000 - mate_in * 10  # White is winning
        else:
            return -10000 - mate_in * 10  # Black is winning
    elif score.mate() == 0:
        return None
        # Return centipawn evaluation
    return score.score()


def best_moves(board, engine, depth=20, num_moves=5):
    """Simplified version - just returns list of Move objects"""
    info = engine.analyse(
        board,
        chess.engine.Limit(depth=depth),
        multipv=num_moves
    )
    
    return {f'{i+1}_best': (pv['pv'][0], pv['score'].white()) for i, pv in enumerate(info)}