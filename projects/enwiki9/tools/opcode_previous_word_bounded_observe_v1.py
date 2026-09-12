"""Isolated original word observer using the canonical bounded-memory audit."""
import hashlib
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import opcode_terminal_bounded_sort_v1 as bounded
import opcode_previous_word_compact_observe_v1 as compact

path = ROOT / 'tools/opcode_previous_word_observe_v1.py'
source = path.read_bytes()
if hashlib.sha256(source).hexdigest() != '33b69c71525fc49fa968c59652744eac9795d9950442ae35e2bdda000a670b0c':
    raise ValueError('original word observer changed')
old = 'from opcode_field_repair_cli_v1 import Audit, feed'
text = source.decode()
assert text.count(old) == 1
word = types.ModuleType(__name__ + '_word')
word.__file__ = str(path)
exec(compile(text.replace(old, 'from opcode_terminal_bounded_sort_v1 import Audit, feed'), str(path), 'exec'), vars(word))
observe = types.FunctionType(compact.observe.__code__,
    dict(vars(compact), word_observe=word.observe), 'observe')
execute = types.FunctionType(compact.execute.__code__,
    dict(vars(compact), observe=observe), 'execute', compact.execute.__defaults__)
