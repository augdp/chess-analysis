import requests
import time

def request_with_agent(url):
    """
    Make a GET request with a User-Agent header to avoid 403 errors.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    return response


def archives(username, base_url):
    """
    Get list of monthly archives available for a user.
    Returns list of URLs for each month's games.
    """
    url = f"{base_url}/player/{username}/games/archives"
    
    response = request_with_agent(url)
    
    if response.status_code == 200:
        archives = response.json()['archives']
        first = "-".join(archives[0].split('/')[-2:])
        last = "-".join(archives[-1].split('/')[-2:])
        print(f"Found monthly archives from {first} to {last}")
        return archives
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return []
    

def from_archive(archive_url):
    """
    Get all games from a specific monthly archive.
    Returns list of game dictionaries.
    """
    response = request_with_agent(archive_url)
    
    if response.status_code == 200:
        return response.json()['games']
    else:
        print(f"❌ Error fetching {archive_url}: {response.status_code}")
        return []
    

def all_recent(username, base_url, num_months=1):
    """
    Get games from the last N months.
    """
    archives_list = archives(username, base_url)
    
    if not archives:
        return []
    
    # Get the last N months
    recent_archives = archives_list[-num_months:]
    
    all_games = []
    for archive_url in recent_archives:
        games = from_archive(archive_url)
        all_games.extend(games)
        time.sleep(0.5)  # Be nice to the API
    
    print(f"\nTotal games fetched: {len(all_games)}")
    return all_games


def filter(games, username, time_control="600", time_class="rapid"):
    """
    Filter games by time control, where rated, with PNG, and with target player playing
    also adds "perspective_color" (the color for the target player) to game data
    """
    filtered_games = []
    for game in games:
        player_color = get_player_color(game, username)
        opponent_color = 'black' if player_color == 'white' else 'white'
        if not player_color:
            continue  # Skip games where the user is not a player

        if game.get('time_control') != time_control:
            continue

        if game.get('time_class') != time_class:
            continue

        if game.get('rated') is not True:
            continue

        if game.get('pgn') is None:
            continue

        game['player_color'] = player_color
        game['opponent_color'] = opponent_color
        filtered_games.append(game)
    
    return filtered_games


def get_player_color(game, username):
    if username.lower() == game['white']['username'].lower():
        return 'white'
    elif username.lower() == game['black']['username'].lower():
        return 'black'
    else:
        return None


def filtered(username, base_url, num_months=1, time_control="600", time_class="rapid"):
    """
    Get games from the last N months filtered by time control.
    """
    all_games = all_recent(username, base_url, num_months)
    
    filtered_games = filter(all_games, username, time_control, time_class)
    
    print(f"Total {time_control} {time_class} games: {len(filtered_games)}")
    return filtered_games