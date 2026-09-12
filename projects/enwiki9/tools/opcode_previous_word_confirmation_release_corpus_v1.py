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
    dict(vars(_base), RAW_LIMIT=RAW_LIMIT, observe_execute=release_execute),
    'execute', _base.execute.__defaults__)
from opcode_previous_word_release_corpus_v1 import main as release_main
def execute_release(module, operation, data, observed=True):
    return execute(module, operation, data, 'D', observed)
main = types.FunctionType(release_main.__code__,
    dict(release_main.__globals__, RAW_LIMIT=RAW_LIMIT, execute=execute_release), 'main')

if __name__ == '__main__':
    main()
