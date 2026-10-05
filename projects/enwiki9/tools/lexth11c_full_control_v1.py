#!/usr/bin/env python3
"""Reproduce the full corpus with a pinned rebuilt donor through the lab."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gamma_enwiki9.adapters.lexth11c_full_control_v1 import main
if __name__ == '__main__':
    raise SystemExit(main())
