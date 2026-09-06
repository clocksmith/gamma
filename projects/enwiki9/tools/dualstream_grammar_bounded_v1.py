#!/usr/bin/env python3
"""Archive-bound repair over the sealed D2GRAM01 codec; no coding change.

Successful archives retain the parent's exact format and bytes. Reject a write
before the complete archive would exceed the decoder's existing acceptance cap.
The inherited file command publishes only closed, successful outputs.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
PARENT_PATH = ROOT / 'tools/dualstream_grammar_v1.py'
PARENT_SHA256 = '9f31a671610aeb2b0f753b13346a06cf1729a4b6b0ce92d2fd7590b3018023bd'
if hashlib.sha256(PARENT_PATH.read_bytes()).hexdigest() != PARENT_SHA256:
    raise RuntimeError('sealed grammar parent source changed')
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_v1 as parent


def __getattr__(name):
    return getattr(parent, name)


class ArchiveWriter:
    def __init__(self, target):
        self.target, self.written = target, 0

    def write(self, data):
        parent.require(self.written + len(data) <= parent.MAX_ARCHIVE,
                       'encoded archive exceeds decoder archive bound')
        count = self.target.write(data)
        parent.require(count == len(data), 'short archive write')
        self.written += count
        return count


def encode_stream(source, target, size, mode='auto', frame_size=parent.MAX_FRAME,
                  config=parent.Config()):
    """A failed stream may contain a prefix; file publication remains atomic."""
    output = ArchiveWriter(target)
    report = parent.encode_stream(source, output, size, mode, frame_size, config)
    parent.require(output.written == report['complete_archive_bytes'],
                   'written archive accounting differs')
    return report


def encode(data, **kwargs):
    output = io.BytesIO()
    report = encode_stream(io.BytesIO(data), output, len(data), **kwargs)
    return output.getvalue(), report


# Reuse the parent's CLI code with two explicit bindings in a private namespace.
# The imported parent's functions and globals remain unchanged.
main = types.FunctionType(parent.main.__code__,
                          {**vars(parent), 'encode_stream': encode_stream,
                           'encode': encode}, name='main')


if __name__ == '__main__':
    main()
