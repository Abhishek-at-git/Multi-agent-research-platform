"""Root CLI runner for Multi-Agent Research Assistant.

Executes research-assistant/main.py seamlessly from the workspace root.
"""

import os
import runpy
import sys
from pathlib import Path

# Insert research-assistant at index 0 of sys.path
APP_DIR = Path(__file__).resolve().parent / "research-assistant"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

os.chdir(str(APP_DIR))

if __name__ == "__main__":
    target_script = APP_DIR / "main.py"
    runpy.run_path(str(target_script), run_name="__main__")
