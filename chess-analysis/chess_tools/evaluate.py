import chess
import chess.engine

from .review import *

class GameEvaluator:
    """
    High-level wrapper that:
    - loads Stockfish
    - parses PGN
    - evaluates positions before/after each move
    - extracts engine lines, metrics, and classification
    - produces a structured output object (moves + summary)
    """

    def __init__(
        self,
        engine_path: str,
        depth: int = 20,
        time_limit: float = 0.5,
        multipv: int = 5,
        roastmode: bool = False,
        engine_options: dict = None
    ):
        """
        Initialize and configure the engine.
        """
        self.engine_path = engine_path
        self.depth = depth
        self.time_limit = time_limit
        self.multipv = multipv
        self.roastmode = roastmode
        self.engine_options = engine_options or {}

        self.engine = None  # stockfish engine instance

        self._init_engine()
    # ------------------------------------------------------------
    # ENGINE INITIALIZATION
    # ------------------------------------------------------------
    def _init_engine(self):
        """
        Creates the underlying chess.engine.SimpleEngine instance and sets options.

        This method:
            - opens the engine
            - sets any provided UCI options
            - prepares the engine for evaluation

        Called automatically by __init__.
        """
        # 1. Open engine
        self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)

        # 2. Set UCI options
        for option, value in self.engine_options.items():
            try:
                self.engine.configure({option: value})
            except Exception as e:
                print(f"[warning] Failed to set engine option {option}={value}: {e}")

        # 3. Validate multipv; some engines require an explicit option
        # if self.multipv > 1:
        #     try:
        #         self.engine.configure({"MultiPV": self.multipv})
        #     except Exception as e:
        #         print(f"[warning] Failed to set MultiPV={self.multipv}: {e}")

    def close(self):
        """
        Cleanly shuts down the engine process.

        Should be called once you're done evaluating games, otherwise
        the engine subprocess may stay alive.
        """
        if self.engine is not None:
            try:
                self.engine.quit()
            except Exception:
                # If normal quit fails, force kill
                self.engine.kill()
            finally:
                self.engine = None

    # ------------------------------------------------------------
    # PGN LOADING
    # ------------------------------------------------------------
    def load_pgn(self, pgn_source):
        """
        Loads a PGN game from:
            - a file path (str)
            - a raw PGN string
            - a file-like object (with .read())

        Returns
        -------
        chess.pgn.Game
            The first game in the PGN.

        Raises
        ------
        ValueError
            If the PGN could not be parsed or is empty.
        """
        # If it's a file path
        if isinstance(pgn_source, str):
            # Case 1: it's a path to a file
            try:
                with open(pgn_source, "r", encoding="utf-8") as f:
                    game = chess.pgn.read_game(f)
            except FileNotFoundError:
                # Case 2: maybe it's a raw PGN string; treat it as inline text
                from io import StringIO
                game = chess.pgn.read_game(StringIO(pgn_source))

        # If file-like
        elif hasattr(pgn_source, "read"):
            # rewind, just in case
            try:
                pgn_source.seek(0)
            except Exception:
                pass

            game = chess.pgn.read_game(pgn_source)

        else:
            raise TypeError(
                "pgn_source must be a file path, raw PGN string, or a file-like object"
            )

        if game is None:
            raise ValueError("Could not parse PGN or PGN is empty.")

        return game

    # ------------------------------------------------------------
    # PER-POSITION METRICS
    # ------------------------------------------------------------
    def compute_development(self, board):
        """Return a normalized development score for one position."""
        return get_development(board)

    def compute_tension(self, board):
        """Return a normalized tension score."""
        return get_tension(board)

    def compute_control(self, board):
        """Return a normalized control score."""
        return get_control(board)

    def compute_mobility(self, board):
        """Return a normalized mobility score."""
        return get_mobility(board)
    
    def compute_eval_cp(self, board):
        """
        Returns a tuple:
            (eval_cp, eval_mate)

        eval_cp  -> integer in centipawns (positive = white is winning)
        eval_mate -> integer indicating mate in N (positive = white mates), 
                    or None if no mate found.
        """
        # Prepare engine limits
        if self.time_limit:
            limits = chess.engine.Limit(time=self.time_limit)
        else:
            limits = chess.engine.Limit(depth=self.depth)

        # Engine analysis
        info = self.engine.analyse(board, limits, multipv=1)

        if isinstance(info, list):
            info = info[0]
        
        score = info["score"].white()  # always convert to white POV

        if score.is_mate():
            return None, score.mate()   # "mate in N"
        else:
            return score.score(), None  # centipawn score
        
    def compute_best_moves(self, board: chess.Board):
        """
        Returns a list of best-move position metric objects.
        Each object is exactly in the standardized format from compute_position_metrics().

        Steps:
            1. Ask engine for MultiPV best lines
            2. For each PV:
                - first move = pv[0]
                - compute SAN
                - compute best_following_line (SAN list)
                - compute resulting board state
                - call compute_position_metrics() with:
                    * that resulting board
                    * san
                    * best_following_line
        """

        # Prepare engine limits
        if self.time_limit:
            limits = chess.engine.Limit(time=self.time_limit)
        else:
            limits = chess.engine.Limit(depth=self.depth)

        # Run MultiPV analysis
        infos = self.engine.analyse(board, limits, multipv=self.multipv)

        best_moves = []

        for info in infos:
            pv = info.get("pv", [])
            if not pv:
                continue

            first_move = pv[0]

            # SAN of the first move
            try:
                san = board.san(first_move)
            except:
                san = None

            # Build SAN PV line
            temp_board = board.copy()
            best_following_line = []
            for mv in pv:
                try:
                    best_following_line.append(temp_board.san(mv))
                except:
                    break
                temp_board.push(mv)

            # Now compute metrics for the resulting position
            # (after pushing the first move)
            resulting_board = board.copy()
            resulting_board.push(first_move)

            metrics = self.compute_position_metrics(
                resulting_board,
                san=san,
                best_following_line=best_following_line
            )

            best_moves.append(metrics)

        return best_moves
    
    def compute_position_metrics(
        self,
        board: chess.Board,
        san: str = None,
        best_following_line: list[str] = None,
    ):
        """
        Compute ALL standardized metrics for a single board position.

        This is the canonical data model used everywhere else:
        
        {
            "development": float,
            "tension": float,
            "control": float,
            "mobility": float,
            "eval_cp": float | None,
            "eval_mate": int | None,
            "fen": str,
            "san": str | None,
            "legal_moves": int,
            "best_following_line": list[str] | None
        }
        """

        # ----- POSITION METRICS -----
        dev_white, dev_black = self.compute_development(board)
        tens_white, tens_black = self.compute_tension(board)
        ctrl_white, ctrl_black = self.compute_control(board)
        mob_white, mob_black = self.compute_mobility(board)

        # Choose the correct side (active player)
        if board.turn:  # white to move
            development = dev_white
            tension = tens_white
            control = ctrl_white
            mobility = mob_white
        else:           # black to move
            development = dev_black
            tension = tens_black
            control = ctrl_black
            mobility = mob_black

        # ----- ENGINE EVALUATION -----
        eval_cp, eval_mate = self.compute_eval_cp(board)

        # ----- LEGAL MOVES COUNT -----
        legal_moves = board.legal_moves.count()

        # ----- RETURN CANONICAL STRUCTURE -----
        return {
            "development": float(development),
            "tension": float(tension),
            "control": float(control),
            "mobility": float(mobility),
            "eval_cp": eval_cp,
            "eval_mate": eval_mate,
            "fen": board.fen(),
            "san": san,
            "legal_moves": legal_moves,
            "best_following_line": best_following_line,
        }
    # ------------------------------------------------------------
    # MOVE ANALYSIS & CLASSIFICATION
    # ------------------------------------------------------------
    def classify_move(self, before, actual, best_moves, board_before_move, move):
        """
        Fully reproduces OpenChess-Insights classification logic.

        Parameters
        ----------
        before : dict 
            Output of compute_position_metrics BEFORE the move
        actual : dict
            Output of compute_position_metrics AFTER the move
        best_moves : list
            List from compute_best_moves() (not used by original logic)
        board_before_move : chess.Board
            The board position before the move is applied
        move : chess.Move
            The move being evaluated (needed for brilliance detection)

        Returns
        -------
        str : 
            One of: 'blunder', 'mistake', 'inaccuracy', 
                    'good', 'excellent', 'best', 'book', 'brilliant'
        """
        # # calculate metrics needed
        # before_cp = before["eval_cp"] if before["eval_cp"] is not None else 0
        # actual_cp = actual["eval_cp"] if actual["eval_cp"] is not None else 0
        # score_diff = actual_cp - before_cp    # improvement (exact repo logic)
        # dev_diff     = actual["development"] - before["development"]
        # tension_diff = actual["tension"]      - before["tension"]
        # mobility_diff= actual["mobility"]     - before["mobility"]
        # control_diff = actual["control"]      - before["control"]

        # call original classificator
        base_classification = inner_classify_move(board_before_move, move).lower()   # repo uses lowercase labels internally
        
        # check if brilliant
        if is_possible_sacrifice(board_before_move, move):
            if base_classification in ['best', 'good', 'excellent']:
                return "brilliant"
        return base_classification
    # ------------------------------------------------------------
    # ENGINE EVALUATION
    # ------------------------------------------------------------
    def evaluate_move(self, board: chess.Board, move: chess.Move):
        """
        Evaluates a single move in exactly the schema the user specified.

        Steps:
            1. Compute position metrics BEFORE the move
            2. Compute best engine moves FROM the before-position
            3. Apply the move and compute actual (AFTER) metrics
            4. Classify the move using before/after/best_moves
            5. Build and return the move evaluation dictionary

        Returns a dict with:
            {
                "move_number": int,
                "half_move_number": int,
                "player": "white" | "black",
                "classification": ...,
                "time_taken": ... (optional if you feed it),
                "depth": self.depth,   # or actual engine depth
                "before": {...},
                "actual_move": {...},
                "best_moves": [...],
            }
        """

        # -----------------------------------------
        # 1. BEFORE MOVE METRICS
        # -----------------------------------------
        before_metrics = self.compute_position_metrics(
            board,
            san=None,                      # no SAN before move
            best_following_line=None
        )

        # -----------------------------------------
        # 2. BEST MOVES FROM THIS POSITION
        # -----------------------------------------
        best_moves = self.compute_best_moves(board)

        # -----------------------------------------
        # 3. APPLY THE MOVE AND GET AFTER METRICS
        # -----------------------------------------
        board_after = board.copy()
        board_after.push(move)

        san = board.san(move)  # SAN for the actual move

        actual_metrics = self.compute_position_metrics(
            board_after,
            san=san,
            best_following_line=None
        )

        # -----------------------------------------
        # 4. CLASSIFICATION
        # -----------------------------------------
        classification = self.classify_move(
            before=before_metrics,
            actual=actual_metrics,
            best_moves=best_moves,
            board_before_move=board,
            move=move
        )

        # -----------------------------------------
        # 5. COMPILE RESULT OBJECT
        # -----------------------------------------

        move_number = board.fullmove_number
        half_move_number = len(board.move_stack) + 1

        player = "white" if board.turn == chess.WHITE else "black"

        result = {
            "move_number": move_number,
            "half_move_number": half_move_number,
            "player": player,
            "classification": classification,
            "time_taken": None,  # you can fill this from PGN clock tags
            "depth": self.depth,
            "before": before_metrics,
            "actual_move": actual_metrics,
            "best_moves": best_moves,
        }

        return result
    # ------------------------------------------------------------
    # GAME-WIDE METRICS (SUMMARY)
    # ------------------------------------------------------------
    def compute_average_cpl(self, side: str, moves: list):
        """
        Compute average centipawn loss (ACPL) for one side.
        This is needed because estimate_elo(acpl, n_moves) in OpenChess-Insights
        takes ACPL as the first argument.

        Inputs:
            side  : "white" or "black"
            moves : list of evaluate_move outputs

        Returns:
            float : average CPL for the side
        """

        # Collect only the moves of the given side
        side_moves = [m for m in moves if m["player"] == side]

        cp_losses = []
        for m in side_moves:
            before_cp = m["before"]["eval_cp"] or 0
            after_cp  = m["actual_move"]["eval_cp"] or 0
            cp_losses.append(abs(after_cp - before_cp))

        if cp_losses:
            return sum(cp_losses) / len(cp_losses)
        else:
            return 0.0

    def compute_player_summary(self, moves, player_color):
        """
        Compute total counts per classification, estimated Elo,
        accuracy, ACL, book moves, etc.

        Returns:
            summary: dict (matches your schema)
        """
        pass

    def compute_accuracy(self, eval_scores):
        return calculate_accuracy(eval_scores)
    
    def compute_estimated_elo(self, acpl, eval_scores):
        return estimate_elo(acpl, eval_scores)
    
    def compute_summary(self, side: str, moves: list, game):
        """
        Compute the summary statistics for one side ("white" or "black"),
        using:
            - OpenChess calculate_accuracy
            - OpenChess estimate_elo
        """

        # -------------------------
        # Extract metadata
        # -------------------------
        username = game.headers["White"] if side == "white" else game.headers["Black"]

        rating_key = "WhiteElo" if side == "white" else "BlackElo"
        try:
            rating = int(game.headers.get(rating_key, None))
        except:
            rating = None

        # -------------------------
        # Build FULL eval_scores for the game
        # -------------------------
        eval_scores = []
        for m in moves:
            cp = m["actual_move"]["eval_cp"]
            if cp is None:
                cp = 0
            eval_scores.append(cp)

        # -------------------------
        # Accuracy (real OI calculation)
        # -------------------------
        white_acc, black_acc = self.compute_accuracy(eval_scores)
        accuracy = white_acc if side == "white" else black_acc
        accuracy = accuracy / 100.0  # convert to 0–1 scale

        # -------------------------
        # ESTIMATED ELO (real OI calculation)
        # -------------------------
        acpl = self.compute_average_cpl(side, moves)
        estimated_elo = self.compute_estimated_elo(acpl, eval_scores)

        # -------------------------
        # Filter moves by side
        # -------------------------
        side_moves = [m for m in moves if m["player"] == side]
        total_moves = len(side_moves)

        # -------------------------
        # Classification counts
        # -------------------------
        counts = {
            "book":       0,
            "brilliant":  0,
            "best":       0,
            "excellent":  0,
            "good":       0,
            "inaccuracy": 0,
            "mistakes":   0,
            "blunders":   0,
        }

        for m in side_moves:
            cls = m["classification"].lower()
            if cls == "mistake": cls = "mistakes"
            if cls == "blunder": cls = "blunders"
            if cls in counts:
                counts[cls] += 1

        # -------------------------
        # Build Final Summary Dict
        # -------------------------
        return {
            "username": username,
            "rating": rating,
            "estimated_elo": estimated_elo,
            "total_moves": total_moves,
            "accuracy": accuracy,
            "avg_centipawn_loss": acpl,

            "book": counts["book"],
            "brilliant": counts["brilliant"],
            "best": counts["best"],
            "excellent": counts["excellent"],
            "good": counts["good"],
            "inaccuracy": counts["inaccuracy"],
            "mistakes": counts["mistakes"],
            "blunders": counts["blunders"],
        }
    # ------------------------------------------------------------
    # ENTIRE GAME EVALUATION
    # ------------------------------------------------------------
    def evaluate_game(self, game):
        """
        Evaluate an entire PGN game.
        
        Steps:
            - Iterate through all moves
            - Evaluate each move using evaluate_move()
            - Build moves list
            - Compute white and black summaries
            - Return full analysis object

        Input:
            game : chess.pgn.Game

        Returns:
            {
                "moves": [...],
                "summary": {
                    "white": {...},
                    "black": {...}
                }
            }
        """

        moves_output = []

        # Starting board
        board = game.board()

        # -----------------------------------------
        # Iterate through all moves in the PGN
        # -----------------------------------------
        for move in game.mainline_moves():
            evaluated = self.evaluate_move(board, move)
            moves_output.append(evaluated)

            # Apply move to board for next iteration
            board.push(move)

        # -----------------------------------------
        # Compute white + black summaries
        # -----------------------------------------
        summary_white = self.compute_summary("white", moves_output, game)
        summary_black = self.compute_summary("black", moves_output, game)

        # -----------------------------------------
        # Final output object
        # -----------------------------------------
        return {
            "moves": moves_output,
            "summary": {
                "white": summary_white,
                "black": summary_black
            }
        }
