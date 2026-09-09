#!/usr/bin/env python3
"""Use the unchanged codec execution with an explicit one-million-byte ceiling."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tools import opcode_event_parse_corpus_v1 as original
from tools.opcode_event_parse_validation_gate_v1 import reuse

# Only the wrapper's two size checks change. The codec already caps raw input
# and reconstructed output at one million bytes; execute is reused unchanged.
main = reuse(original.main, [
    ("(250000 if args.operation == 'encode' else 33554432)",
     "(1000000 if args.operation == 'encode' else 33554432)"),
    ("len(out) > 250000", "len(out) > 1000000")], vars(original))


if __name__ == '__main__':
    main()
