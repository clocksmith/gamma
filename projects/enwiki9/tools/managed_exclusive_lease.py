#!/usr/bin/env python3
"""Compatibility import; pre-extraction bytes are retained in framework-closures."""
import sys
try:
    from . import _enwiki9_bootstrap
except ImportError:
    import _enwiki9_bootstrap
from gamma_enwiki9.execution import lease as _implementation
sys.modules[__name__] = _implementation
