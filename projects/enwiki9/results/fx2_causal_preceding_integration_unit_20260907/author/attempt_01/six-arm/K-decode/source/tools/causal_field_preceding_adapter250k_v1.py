#!/usr/bin/env python3
"""Explicit 250KB scope for the frozen immediately preceding field selector.

This version changes the declared raw bound, not parser, table or WRT behavior.
Its factory preserves original P and original first-field T (named O) exactly.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
from types import ModuleType

TOOLS = Path(__file__).resolve().parent
SELECTOR_SHA256 = "d48c6ac00defe186b3c2f9982140d78d88036c3ff8d11386cbbf690ae1c4dda9"
POLICY = "causal-field-immediately-preceding-wrt250k-v1"
ORIGINAL_POLICY = "causal-field-original-first-wrt-v1"
MAX_RAW = 250000

_path = TOOLS / "causal_field_preceding_selector_v1.py"
_source = _path.read_bytes()
if hashlib.sha256(_source).hexdigest() != SELECTOR_SHA256:
    raise ValueError("frozen immediately preceding selector source changed")
selector = ModuleType(__name__ + ".frozen_selector")
selector.__file__ = str(_path)
sys.modules[selector.__name__] = selector
exec(compile(_source, str(_path), "exec"), selector.__dict__)
original = selector.base


class Adapter(selector.Adapter):
    policy_id = POLICY

    def __init__(self, words, arm="T", raw_limit=MAX_RAW):
        original.require(type(raw_limit) is int and 0 <= raw_limit <= MAX_RAW,
                         "preceding250k expected raw length exceeds bound")
        original.require(isinstance(arm, str) and len(arm) == 1 and arm in "KTRS", "unknown adjacent arm")
        # Explicitly initialize the sealed WRT base under this version's bound.
        # The sealed synthetic initializer continues to reject raw lengths>8192.
        original.Adapter.__init__(self, words, arm=arm, raw_limit=raw_limit)


def make_adapter(words, *, arm, raw_limit):
    original.require(isinstance(arm, str) and len(arm) == 1 and arm in "PKTORS", "unknown replay arm")
    if arm in "PO":
        return original.Adapter(words, arm="P" if arm == "P" else "T", raw_limit=raw_limit)
    return Adapter(words, arm=arm, raw_limit=raw_limit)


def source_inventory():
    paths = [Path(__file__), *(TOOLS.parent / row["path"] for row in selector.source_inventory())]
    return [{"path": str(path.relative_to(TOOLS.parent)), "bytes": path.stat().st_size,
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(paths)]
