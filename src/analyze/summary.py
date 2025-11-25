# uses: classify.py, accuracy.py

def player_move_subset(moves, color):
def compute_avg_cpl(moves):
def compute_accuracy(moves):
def estimate_elo(avg_cpl, n_moves):
def count_classifications(moves, color):
def build_summary(moves, game_metadata):

def calculate_accuracy(eval_scores):

    eval_scores = [0] + eval_scores
    def calculate_win_percentage(cp_eval, color):
        if color == 'w':
            return 50 + 50 * (2 / (1 + np.exp(-0.00368208 * cp_eval)) - 1)
        elif color == 'b':
            return 50 + 50 * (2 / (1 + np.exp(0.00368208 * cp_eval)) - 1)
        
    white_win_percentages = [calculate_win_percentage(s, 'w') for s in eval_scores]
    black_win_percentages = [100-p for p in white_win_percentages]

    # Accuracy% = 103.1668 * exp(-0.04354 * (winPercentBefore - winPercentAfter)) - 3.1669
    white_accuracies = []
    black_accuracies = []
    for i in range(len(white_win_percentages)-1):
        #100.03072339664806 * exp(-0.10082980372791278 * x) + -0.030767264030683358
        if i%2 == 0:
            win_delta = white_win_percentages[i] - white_win_percentages[i+1]
            if win_delta <= 0:
                white_accuracies.append(100)
            else:
                accuracy = 100.0307234 * np.exp(-0.1008298 * (win_delta)) - 0.03076726
                white_accuracies.append(accuracy)
        else:
            win_delta = black_win_percentages[i] - black_win_percentages[i+1]
            if win_delta <= 0:
                black_accuracies.append(100)
            else:
                accuracy = 100.0307234 * np.exp(-0.1008298 * (win_delta)) - 0.03076726
                black_accuracies.append(accuracy)

    return np.mean(white_accuracies), np.mean(black_accuracies)
