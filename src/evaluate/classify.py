# uses: review.py

def classify_score_only(score_diff):
def classify_move(before_metrics, after_metrics):
def is_possible_sacrifice(board_before, move):
def is_brilliant(before, after, board_before, move):

def classify_move(board: chess.Board, move):

    points_gained = calculate_points_gained_by_move(board, move)

    if type(points_gained) == str:
        # quite redundant put im putting it for clarity
        if 'mates' in points_gained: 
            return points_gained
        elif 'continues gets mated' in points_gained:
            return points_gained
        elif 'gets mated' in points_gained:
            return points_gained
        elif 'lost mate' in points_gained:
            return points_gained

    if (points_gained >= -20):
        return 'excellent'
    elif (points_gained < -20) and (points_gained >= -100):
        return 'good'
    elif (points_gained < -100) and (points_gained >= -250):
        return 'inaccuracy'
    elif (points_gained < -250) and (points_gained >= -450):
        return 'mistake'
    else:
        return 'blunder'
