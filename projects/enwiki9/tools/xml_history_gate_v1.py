"""Compatibility entrypoint for the maintained XML/history experiment adapter."""
from pathlib import Path
import sys

import _enwiki9_bootstrap

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gamma_enwiki9.adapters.xml_history_comparison import main

if __name__ == '__main__':
    main()
