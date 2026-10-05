#!/usr/bin/env python3
"""Run an offline lexth11c rebuild through the registered lab infrastructure gate."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from gamma_enwiki9.adapters.lexth11c_build import main
if __name__=='__main__':raise SystemExit(main())
