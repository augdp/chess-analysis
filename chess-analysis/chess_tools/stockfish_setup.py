import os
import platform
import chess
import chess.engine
import chess.pgn
import asyncio
import sys



# Try to detect if stockfish is accessible
def check_path(path):
    set_coherent_event_loop()
    print(f"Checking path: {path}")

    if os.path.exists(path):
        print(f"✅ File exists at: {path}")
        print(f"✅ File size: {os.path.getsize(path):,} bytes")
    else:
        raise Exception(f"❌ Stockfish not found at: {path}")
    

def set_coherent_event_loop():
    if sys.platform == 'win32':
        # This fixes the NotImplementedError when using chess.engine on Windows in Jupyter
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def engine(path):
    return chess.engine.SimpleEngine.popen_uci(path)


def basic_setup():
    set_coherent_event_loop()
    return None

