from dotenvx import load_dotenvx
import runpy
import sys

load_dotenvx()
print("Starting bot...", flush=True)
sys.stdout.flush()
sys.stderr.flush()
runpy.run_path("meta_strategy_bot.py", run_name="__main__")
