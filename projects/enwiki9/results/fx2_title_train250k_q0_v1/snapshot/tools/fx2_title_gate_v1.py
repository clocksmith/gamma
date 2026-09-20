"""Compatibility entrypoint for the frozen matched title-training recipe."""
import _enwiki9_bootstrap
from gamma_enwiki9.adapters.fx2_title_gate import main

if __name__ == '__main__':
    main()
