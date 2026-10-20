# src/run.py
import os
import runpy
import sys

PLUGIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin")

sys.path.insert(0, os.path.join(PLUGIN_DIR, "site-packages"))
runpy.run_path(PLUGIN_DIR, run_name="__main__")
