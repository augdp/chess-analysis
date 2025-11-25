# uses: cp_eval or stockfish
# (or independent model if you swap it later)

class ExpWinEvaluator:
    def __init__(self, cp_evaluator=None, k=0.004):
    def evaluate(self, board):
        # returns { "exp_win": x, "eval_cp": cp, "eval_mate": mate }
    def cp_to_expwin(self, cp):
