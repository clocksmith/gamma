#!/usr/bin/env python3
"""Run the registered isolated donor GPU diagnostic."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from gamma_enwiki9.adapters.lexth11c_gpu_native_domain_v2 import main
if __name__=='__main__':raise SystemExit(main())
