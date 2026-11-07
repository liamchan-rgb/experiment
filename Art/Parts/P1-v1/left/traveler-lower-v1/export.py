#!/usr/bin/env python3
"""Rebuild the shared left traveler trousers and boots plus its paired shirt preview."""
from pathlib import Path
import runpy
script=Path(__file__).resolve().parents[1]/'forester-v1'/'export.py'
runpy.run_path(str(script),run_name='__main__')
