"""Root Streamlit runner for Multi-Agent Research Assistant.

Executes research-assistant/app.py seamlessly from the workspace root.
Run with: streamlit run app.py
"""

import os
import runpy
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent / "research-assistant"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

os.chdir(str(APP_DIR))

target_app = APP_DIR / "app.py"
runpy.run_path(str(target_app), run_name="__main__")
