from dotenvx import load_dotenvx
import runpy

load_dotenvx()
runpy.run_path("price_action_bot.py", run_name="__main__")
