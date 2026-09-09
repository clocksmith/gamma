#!/usr/bin/env python3
"""Reuse the bounded corpus CLI with the source-integrated P/K/D/S observer."""
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from opcode_previous_word_release_corpus_v1 import _base
from opcode_previous_word_compact_observe_v1 import execute as observe_execute

load = _base.load
RAW_LIMIT, ARCHIVE_LIMIT = _base.RAW_LIMIT, _base.ARCHIVE_LIMIT
execute = types.FunctionType(_base.execute.__code__,
    dict(vars(_base), observe_execute=observe_execute), 'execute', _base.execute.__defaults__)
main = types.FunctionType(_base.main.__code__, dict(vars(_base), execute=execute), 'main')


if __name__ == '__main__':
    main()
