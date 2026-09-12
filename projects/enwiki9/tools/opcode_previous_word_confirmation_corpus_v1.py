#!/usr/bin/env python3
"""Fixed 1MB bounds around the unchanged previous-word codec and observer."""
from pathlib import Path
import sys
import types
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from opcode_previous_word_release_corpus_v1 import _base, release_execute
from opcode_previous_word_compact_observe_v1 import execute as compact_execute
RAW_LIMIT = 1000000
execute = types.FunctionType(_base.execute.__code__,
    dict(vars(_base), RAW_LIMIT=RAW_LIMIT, observe_execute=compact_execute),
    'execute', _base.execute.__defaults__)
main = types.FunctionType(_base.main.__code__,
    dict(vars(_base), RAW_LIMIT=RAW_LIMIT, execute=execute), 'main')

if __name__ == '__main__':
    main()
