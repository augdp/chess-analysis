# uses: 
    # parse.py
    # review.py
    # classify.py
    # cp_eval.py OR expwin_eval.py

class GameEvaluator:

    def __init__(
        self,
        evaluator_model,        # cp or expwin
        multipv=1,
        depth=18,
        time_limit=None,
        stockfish_path=None
    ):

    def evaluate_game(self, game):
    def evaluate_move(self, board, move):
    def compute_position_metrics(self, board, san=None, best_line=None):
    def compute_best_moves(self, board):
    def classify(self, before, after, best_moves, board_before, move):
    def build_move_record(self, ...):
