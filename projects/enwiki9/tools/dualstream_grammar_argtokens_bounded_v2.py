#!/usr/bin/env python3
"""Apply the existing archive-write guard to D2GRAM02 without changing its bytes.

The measured argument codec remains immutable. This separately identified entry
point rejects oversized archives before atomic file publication, including tiny
frames outside the fixed 65536-byte corpus experiment.
"""
from pathlib import Path
import sys
import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import dualstream_grammar_argtokens_v2 as parent
from tools import dualstream_grammar_bounded_v1 as repair

# Rebind the existing guard implementation, not the measured modules' globals.
namespace = {**vars(repair), 'parent': parent.core}
def bind(function):
    return types.FunctionType(function.__code__, namespace, function.__name__, function.__defaults__)

ArchiveWriter = type('ArchiveWriter', (), {name: bind(getattr(repair.ArchiveWriter, name))
                                         for name in ('__init__', 'write')})
namespace['ArchiveWriter'] = ArchiveWriter
encode_stream = namespace['encode_stream'] = bind(repair.encode_stream)
encode = namespace['encode'] = bind(repair.encode)
main = types.FunctionType(parent.core.main.__code__,
                          {**vars(parent.core), 'encode_stream': encode_stream, 'encode': encode}, 'main')

def __getattr__(name):
    return getattr(parent, name)

if __name__ == '__main__':
    main()
