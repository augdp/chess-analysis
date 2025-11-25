# src/setup/stockfish.py

import chess
import chess.engine
import subprocess
import os
import sys

class StockfishEngine:
    """
    Wrapper around a Stockfish (or any UCI) engine binary.
    Manages startup, analysis, and shutdown.
    """
    def __init__(self, engine_path: str, timeout: float = None):
        """
        engine_path : path to stockfish binary
        timeout : optional timeout for engine commands
        """
        self.engine_path = engine_path
        self.timeout = timeout
        self.engine: chess.engine.SimpleEngine | None = None

    def start(self):
        # On Windows, avoid opening a console window
        popen_args = {}
        if sys.platform.startswith("win"):
            # Use CREATE_NO_WINDOW flag
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            popen_args["startupinfo"] = startupinfo
        self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path, **popen_args)

    def analyze(self, board: chess.Board, depth: int = None, time: float = None, multipv: int = 1):
        """
        Analyze a position. Returns engine info dict or list (multipv).
        """
        if self.engine is None:
            self.start()

        limits = chess.engine.Limit()
        if time is not None:
            limits = chess.engine.Limit(time=time)
        elif depth is not None:
            limits = chess.engine.Limit(depth=depth)

        info = self.engine.analyse(board, limits, multipv=multipv)
        # If engine returns a list when multipv=1, standardize to single dict
        if isinstance(info, list):
            return info
        else:
            return [info]

    def stop(self):
        if self.engine is not None:
            try:
                self.engine.quit()
            except Exception:
                self.engine.kill()
            finally:
                self.engine = None
