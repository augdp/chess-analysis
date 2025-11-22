

def _add_basic_structure(summary, df):
    """Add basic statistics to the summary dictionary."""
    summary['total_games'] = len(df)
    summary['wins'] = len(df[df['outcome'] == 'win'])
    summary['losses'] = len(df[df['outcome'] == 'loss'])
    summary['draws'] = len(df[df['outcome'] == 'draw'])

    return summary


def summarize_performance(df):
    """
    Generate a comprehensive performance summary for chess games.
    
    Args:
        df: DataFrame with columns: date, color, outcome, your_rating, opponent_rating,
            rating_diff, opponent, num_moves, opening_code, opening_name, time_control, url
    
    Returns:
        dict: Dictionary containing various performance metrics
    """
    summary = {}
    
    # Basic statistics + Win rates
    summary = _add_basic_structure(summary, df)
    if not summary['total_games']:
        return None

    # Win rates
    summary['win_rate'] = (summary['wins'] / summary['total_games']) * 100
    summary['loss_rate'] = (summary['losses'] / summary['total_games']) * 100
    summary['draw_rate'] = (summary['draws'] / summary['total_games']) * 100
    
    # Performance by color
    white_games = df[df['color'] == 'white']
    black_games = df[df['color'] == 'black']
    
    summary['white_games'] = len(white_games)
    summary['white_wins'] = len(white_games[white_games['outcome'] == 'win'])
    summary['white_win_rate'] = (summary['white_wins'] / summary['white_games'] * 100) if summary['white_games'] > 0 else 0
    
    summary['black_games'] = len(black_games)
    summary['black_wins'] = len(black_games[black_games['outcome'] == 'win'])
    summary['black_win_rate'] = (summary['black_wins'] / summary['black_games'] * 100) if summary['black_games'] > 0 else 0
    
    # Rating analysis
    summary['current_rating'] = df['your_rating'].iloc[0]  # Most recent game (df is sorted by date desc)
    summary['highest_rating'] = df['your_rating'].max()
    summary['lowest_rating'] = df['your_rating'].min()
    summary['avg_rating'] = df['your_rating'].mean()
    summary['rating_change'] = df['your_rating'].iloc[0] - df['your_rating'].iloc[-1]
    
    # Opponent analysis
    summary['avg_opponent_rating'] = df['opponent_rating'].mean()
    summary['strongest_opponent'] = df['opponent_rating'].max()
    summary['weakest_opponent'] = df['opponent_rating'].min()
    
    # Performance against stronger/weaker opponents
    stronger_opponents = df[df['rating_diff'] < 0]  # Negative means opponent is stronger
    weaker_opponents = df[df['rating_diff'] > 0]
    even_opponents = df[df['rating_diff'] == 0]
    
    summary['games_vs_stronger'] = len(stronger_opponents)
    summary['wins_vs_stronger'] = len(stronger_opponents[stronger_opponents['outcome'] == 'win'])
    summary['win_rate_vs_stronger'] = (summary['wins_vs_stronger'] / summary['games_vs_stronger'] * 100) if summary['games_vs_stronger'] > 0 else 0
    
    summary['games_vs_weaker'] = len(weaker_opponents)
    summary['wins_vs_weaker'] = len(weaker_opponents[weaker_opponents['outcome'] == 'win'])
    summary['win_rate_vs_weaker'] = (summary['wins_vs_weaker'] / summary['games_vs_weaker'] * 100) if summary['games_vs_weaker'] > 0 else 0
    
    summary['games_vs_even'] = len(even_opponents)
    summary['wins_vs_even'] = len(even_opponents[even_opponents['outcome'] == 'win'])
    summary['win_rate_vs_even'] = (summary['wins_vs_even'] / summary['games_vs_even'] * 100) if summary['games_vs_even'] > 0 else 0
    
    # Game length analysis
    summary['avg_moves'] = df['num_moves'].mean()
    summary['shortest_game'] = df['num_moves'].min()
    summary['longest_game'] = df['num_moves'].max()
    
    # Win/loss by game length
    wins_df = df[df['outcome'] == 'win']
    losses_df = df[df['outcome'] == 'loss']
    summary['avg_moves_in_wins'] = wins_df['num_moves'].mean() if len(wins_df) > 0 else 0
    summary['avg_moves_in_losses'] = losses_df['num_moves'].mean() if len(losses_df) > 0 else 0
    
    # Opening analysis
    summary['unique_openings'] = df['opening_name'].nunique()
    summary['most_played_opening'] = df['opening_name'].value_counts().index[0] if len(df) > 0 else 'N/A'
    summary['most_played_opening_count'] = df['opening_name'].value_counts().iloc[0] if len(df) > 0 else 0
    
    # Best opening (by win rate, minimum 3 games)
    opening_stats = df.groupby('opening_name').agg({
        'outcome': lambda x: (x == 'win').sum() / len(x) * 100,
        'opening_name': 'size'
    }).rename(columns={'outcome': 'win_rate', 'opening_name': 'count'})
    opening_stats = opening_stats[opening_stats['count'] >= 3].sort_values('win_rate', ascending=False)
    
    if len(opening_stats) > 0:
        summary['best_opening'] = opening_stats.index[0]
        summary['best_opening_win_rate'] = opening_stats['win_rate'].iloc[0]
        summary['best_opening_games'] = opening_stats['count'].iloc[0]
    else:
        summary['best_opening'] = 'N/A'
        summary['best_opening_win_rate'] = 0
        summary['best_opening_games'] = 0
    
    # Streaks
    summary['current_streak'] = calculate_current_streak(df)
    summary['longest_win_streak'] = calculate_longest_streak(df, 'win')
    summary['longest_loss_streak'] = calculate_longest_streak(df, 'loss')
    
    return summary


def calculate_longest_streak(df, outcome_type):
    """Calculate longest streak of a specific outcome type."""
    if len(df) == 0:
        return 0
    
    max_streak = 0
    current_streak = 0
    
    # Iterate from oldest to newest
    for outcome in df['outcome'].iloc[::-1]:
        if outcome == outcome_type:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    
    return max_streak


def calculate_current_streak(df):
    """Calculate current win/loss streak from most recent games."""
    if len(df) == 0:
        return "No games"
    
    last_outcome = df['outcome'].iloc[0]
    streak_count = 1
    
    for outcome in df['outcome'].iloc[1:]:
        if outcome == last_outcome:
            streak_count += 1
        else:
            break
    
    return f"{streak_count} {last_outcome}{'s' if streak_count > 1 else ''}"


def print_performance_summary(summary):
    """Pretty print the performance summary."""
    print("=" * 70)
    print("📊 CHESS PERFORMANCE SUMMARY")
    print("=" * 70)
    
    print(f"\n{'OVERALL STATISTICS':^70}")
    print("-" * 70)
    print(f"Total Games:        {summary['total_games']}")
    print(f"Wins:               {summary['wins']} ({summary['win_rate']:.1f}%)")
    print(f"Losses:             {summary['losses']} ({summary['loss_rate']:.1f}%)")
    print(f"Draws:              {summary['draws']} ({summary['draw_rate']:.1f}%)")
    
    print(f"\n{'RATING STATISTICS':^70}")
    print("-" * 70)
    print(f"Current Rating:     {summary['current_rating']}")
    print(f"Highest Rating:     {summary['highest_rating']}")
    print(f"Lowest Rating:      {summary['lowest_rating']}")
    print(f"Average Rating:     {summary['avg_rating']:.1f}")
    print(f"Rating Change:      {summary['rating_change']:+.0f} (over {summary['total_games']} games)")
    
    print(f"\n{'PERFORMANCE BY COLOR':^70}")
    print("-" * 70)
    print(f"As White:           {summary['white_wins']}/{summary['white_games']} wins ({summary['white_win_rate']:.1f}%)")
    print(f"As Black:           {summary['black_wins']}/{summary['black_games']} wins ({summary['black_win_rate']:.1f}%)")
    
    print(f"\n{'OPPONENT STRENGTH ANALYSIS':^70}")
    print("-" * 70)
    print(f"Avg Opponent:       {summary['avg_opponent_rating']:.0f}")
    print(f"Strongest Opponent: {summary['strongest_opponent']}")
    print(f"Weakest Opponent:   {summary['weakest_opponent']}")
    print()
    print(f"vs Stronger ({summary['games_vs_stronger']} games):  {summary['wins_vs_stronger']} wins ({summary['win_rate_vs_stronger']:.1f}%)")
    print(f"vs Weaker ({summary['games_vs_weaker']} games):    {summary['wins_vs_weaker']} wins ({summary['win_rate_vs_weaker']:.1f}%)")
    print(f"vs Equal ({summary['games_vs_even']} games):     {summary['wins_vs_even']} wins ({summary['win_rate_vs_even']:.1f}%)")
    
    print(f"\n{'GAME LENGTH STATISTICS':^70}")
    print("-" * 70)
    print(f"Average Moves:      {summary['avg_moves']:.1f}")
    print(f"Shortest Game:      {summary['shortest_game']} moves")
    print(f"Longest Game:       {summary['longest_game']} moves")
    print(f"Avg in Wins:        {summary['avg_moves_in_wins']:.1f} moves")
    print(f"Avg in Losses:      {summary['avg_moves_in_losses']:.1f} moves")
    
    print(f"\n{'OPENING STATISTICS':^70}")
    print("-" * 70)
    print(f"Unique Openings:    {summary['unique_openings']}")
    print(f"Most Played:        {summary['most_played_opening']} ({summary['most_played_opening_count']} games)")
    if summary['best_opening'] != 'N/A':
        print(f"Best Opening:       {summary['best_opening']}")
        print(f"                    {summary['best_opening_win_rate']:.1f}% win rate ({int(summary['best_opening_games'])} games)")
    
    print(f"\n{'STREAKS':^70}")
    print("-" * 70)
    print(f"Current Streak:     {summary['current_streak']}")
    print(f"Longest Win Streak: {summary['longest_win_streak']} games")
    print(f"Longest Loss Streak:{summary['longest_loss_streak']} games")
    
    print("\n" + "=" * 70)