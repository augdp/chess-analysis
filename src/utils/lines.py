# src/utils/lines.py

import chess

def pv_to_san_list(board: chess.Board, pv_moves: list[chess.Move]) -> list[str]:
    """
    Given a board and a principal variation (list of Move objects),
    return the SAN representation of each move in the line.
    """
    san_line = []
    temp = board.copy()
    for mv in pv_moves:
        try:
            san = temp.san(mv)
        except Exception:
            break
        san_line.append(san)
        temp.push(mv)
    return san_line

def limit_line_length(san_line: list[str], max_len: int = 12) -> list[str]:
    """
    Truncate the SAN line to a maximum number of plies.
    Useful to avoid extremely long PVs.
    """
    return san_line[:max_len]

def extract_pv_from_info(info: dict) -> list[chess.Move]:
    """
    Given an engine info dict, return the PV (principal variation) as a list of Moves,
    or empty list if none.
    """
    return info.get("pv", [])

def build_best_lines(board: chess.Board, infos: list[dict], max_lines: int = 5, max_pv: int = 12):
    """
    Given multiple engine info dicts (multipv), return a list of dictionaries:
      {
         "san": <first move SAN>,
         "pv": <san_line list>,
         "depth": info.get("depth"),
         "score": info.get("score"),
         ...
      }
    Useful for “best_moves” output in your evaluator.
    """
    best = []
    for info in infos[:max_lines]:
        pv_moves = extract_pv_from_info(info)
        if not pv_moves:
            continue
        san_line = pv_to_san_list(board, pv_moves)
        san_line = limit_line_length(san_line, max_pv)
        first_move_san = san_line[0] if san_line else None
        best.append({
            "first_move_san": first_move_san,
            "san_line": san_line,
            "score": info.get("score"),
            "depth": info.get("depth"),
            "pv_moves": pv_moves,
        })
    return best
