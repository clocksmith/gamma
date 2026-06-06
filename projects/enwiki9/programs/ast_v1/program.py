"""ast_v1 — Phase A of Track B (AST-driven compression).

Pipeline:
  bytes
    -> deterministic AST tokenizer (XML, [[wikilink]], {{template}}, literal)
    -> serialized opcode stream
    -> lzma --extreme -9 (kill-comparison back-end)

The kill condition for Phase A is whether the AST representation, fed
through the same back-end as `baseline_lzma`, beats raw bytes through
that same back-end. If it doesn't, the structural bookkeeping costs
more than the typed-stream isolation saves, and Track B retires.

Reversibility and determinism: see ast_parser.py.
"""

from __future__ import annotations

import lzma
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ast_parser  # noqa: E402

PRESET = 9 | lzma.PRESET_EXTREME


def compress(data: bytes) -> bytes:
    serialized, _stats = ast_parser.encode(data)
    return lzma.compress(serialized, preset=PRESET)


def decompress(data: bytes) -> bytes:
    serialized = lzma.decompress(data)
    return ast_parser.decode(serialized)
