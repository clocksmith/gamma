"""Example candidate plug-in. Not a real codec: it stores each record XORed with 0x5A.

It exists to show the adapter shape and to test the plug-in path, including native timing:

    python3 run_fair_baselines.py --train TRAIN --test TEST --out out.json \
        --candidate examples/candidate_example.py:XorCandidate

Archive layout: "XOR1", u32 record count, one u32 end offset per record, then the XORed records.
"""
from __future__ import annotations

import hashlib
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEY = 0x5A


class _Reader:
    def __init__(self, archive: bytes):
        if archive[:4] != b'XOR1':
            raise ValueError('not an XOR1 archive')
        (self.count,) = struct.unpack_from('<I', archive, 4)
        self.ends = struct.unpack_from(f'<{self.count}I', archive, 8)
        self.body = archive[8 + 4 * self.count:]

    def decode(self, i: int, cap: int = 0) -> bytes:
        start = self.ends[i - 1] if i else 0
        return bytes(b ^ KEY for b in self.body[start:self.ends[i]])


class XorCandidate:
    name = 'example-xor'
    label = 'example plug-in: records XORed with 0x5A, 4 index bytes per record (not a real codec)'

    def train(self, train_records, train_groups):
        return {'note': 'nothing to fit'}

    def encode(self, records, groups):
        ends, cur = [], 0
        for r in records:
            cur += len(r)
            ends.append(cur)
        header = b'XOR1' + struct.pack('<I', len(records))
        index = struct.pack(f'<{len(records)}I', *ends)
        body = bytes(b ^ KEY for b in b''.join(records))
        return {
            'archive': header + index + body,
            'accounting': {'header': len(header), 'model': 0, 'index': len(index), 'framing': 0, 'payload': len(body)},
            'like_for_like_bytes': len(header) + len(index) + len(body),
        }

    def open(self, archive):
        return _Reader(archive)

    def native_decoder(self):
        """Build the C decoder next to the harness's own helper (outside the repository)."""
        src = HERE / 'candidate_example_native.c'
        build_dir = Path(os.environ.get('FAIR_BASELINES_BUILD_DIR') or Path(tempfile.gettempdir()) / 'fair-baselines-v1-build')
        tag = hashlib.sha256(src.read_bytes()).hexdigest()[:12]
        lib = build_dir / f'libfbexample-{tag}.{"dylib" if sys.platform == "darwin" else "so"}'
        if not lib.is_file():
            build_dir.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run([os.environ.get('CC', 'cc'), '-O3', '-fPIC', '-shared', str(src), '-o', str(lib)],
                                  capture_output=True, text=True)
            if proc.returncode != 0:
                return None   # no compiler: the harness falls back to Python-loop timing and says so
        return {'library': str(lib), 'open': 'xor_open', 'decode': 'xor_decode', 'close': 'xor_close'}
