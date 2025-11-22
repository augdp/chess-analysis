import chess
import chess.engine
import chess.pgn
import io
from datetime import datetime
import math
import pandas as pd

def pgn_games(games):
    """
    Parse PGN strings into chess.pgn.Game objects.
    """
    parsed_games = []
    
    for i, game_data in enumerate(games):
        try:
            pgn_string = game_data['pgn']
            pgn_io = io.StringIO(pgn_string)
            game = chess.pgn.read_game(pgn_io)
            
            if game is not None:
                # Add metadata to the game object for easy access
                game.metadata = game_data
                parsed_games.append(game)
        except Exception as e:
            print(f"⚠️ Error parsing game {i}: {e}")
            continue
    
    print(f"Parsed {len(parsed_games)} games")
    return parsed_games


def generate_dataframe(parsed_games):
    """
    Create a pandas DataFrame with game summaries.
    """
    data = []
    
    for game in parsed_games:
        metadata = game.metadata
        
        # Count moves (full moves: 1 white move + 1 black move = 1 move)
        # Use ceiling division so if White checkmates on move 3, it counts as 3 moves, not 2
        moves = list(game.mainline_moves())
        num_moves = math.ceil(len(moves) / 2)  # Ceiling division: rounds up for odd number of half-moves
        
        # Get opening info
        opening = game.headers.get('ECO', 'Unknown')
        opening_name = game.headers.get('ECOUrl', 'Unknown')
        if opening_name != 'Unknown' and '/' in opening_name:
            opening_name = opening_name.split('/')[-1].replace('-', ' ').title()
        
        # Determine game outcome
        outcome = "win" #game_outcome(game)
        
        # Convert timestamp
        date = datetime.fromtimestamp(metadata['end_time'])
        
        data.append({
            'date': date,
            'color': metadata['player_color'],
            'outcome': outcome,
            'your_rating': metadata[metadata['player_color']]['rating'],
            'opponent_rating': metadata[metadata['opponent_color']]['rating'],
            'rating_diff': metadata[metadata['player_color']]['rating'] - metadata[metadata['opponent_color']]['rating'] if isinstance(metadata[metadata['player_color']]['rating'], int) and isinstance(metadata[metadata['opponent_color']]['rating'], int) else 0,
            'opponent': metadata[metadata['opponent_color']]['username'],
            'num_moves': num_moves,
            'opening_code': opening,
            'opening_name': opening_name,
            'time_control': metadata['time_control'],
            'url': metadata['url'],
            'game_object': game  # Keep reference to game object
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values('date', ascending=False).reset_index(drop=True)
    
    return df