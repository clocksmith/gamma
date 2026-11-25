"""Plug-in point for a candidate codec.

A candidate is measured by the same code as the baselines: same train and test records, same
verification, same accounting categories, same timing loop.

Write a Python file with a class like this and pass `--candidate path/to/file.py:ClassName`:

    class MyCodec:
        name = 'my-codec'
        label = 'one line saying what it is'

        def train(self, train_records, train_groups):
            # list[bytes], list[str] | None. Fit everything here. Test records are not available yet.
            return {'anything': 'you want recorded'}          # or None

        def encode(self, records, groups):
            # Return the archive and say which of its bytes fall in which category.
            return {
                'archive': archive_bytes,
                'accounting': {'header': h, 'model': m, 'index': i, 'framing': f, 'payload': p},
                # optional: the size this codec's own benchmark would report, for a like-for-like column
                'like_for_like_bytes': n,
                # optional: a second serialization that uses a compact index
                'archive_compact_index': other_bytes,
                'accounting_compact_index': {...},
            }

        def open(self, archive):
            # Return an object with decode(i) -> bytes (and optionally close()).
            # It is given the archive bytes only: everything needed to decode must be inside them.
            ...

        # Optional. Without it lookups are timed in a Python loop and the timing is labelled as
        # not comparable with the native numbers.
        def native_decoder(self):
            return {'library': '/path/to/lib.dylib', 'open': 'my_open', 'decode': 'my_decode', 'close': 'my_close'}

Native ABI (C):

    void  *my_open(const uint8_t *archive, size_t len);     /* NULL on failure */
    size_t my_decode(void *ctx, uint32_t i, uint8_t *dst, size_t cap);   /* record length, (size_t)-1 on error */
    void   my_close(void *ctx);

`my_decode` is called through the same function pointer type, from the same loop, as every baseline.

What the harness checks and what it takes on trust:
  - checked: the accounting categories sum to len(archive); every record decoded on its own, in
    random order, equals the original bytes (through `open().decode` and, if given, the native decoder)
  - on trust: how the candidate splits its bytes between the categories, and that `train` did not
    keep test data (it is called before the test records are handed over)
"""
from __future__ import annotations

import ctypes
import importlib.util
from pathlib import Path
from typing import Sequence

import fb_core as C
from fb_codecs import Codec

FB_ERR = ctypes.c_size_t(-1).value
CATEGORIES = ('header', 'model', 'index', 'framing', 'payload')


class OpaqueEncoded:
    """Archive produced by a candidate; the harness does not know its layout."""

    def __init__(self, result: dict):
        self.result = result
        self.detail = {'accounting_split': 'reported by the candidate; only the total is checked'}
        self.archive = bytes(result['archive'])

    @staticmethod
    def _acct(raw: dict, archive: bytes) -> C.Accounting:
        missing = [k for k in CATEGORIES if k not in raw]
        if missing:
            raise ValueError(f'candidate accounting lacks {missing}')
        acct = C.Accounting(**{k: int(raw[k]) for k in CATEGORIES})
        if acct.total != len(archive):
            raise ValueError(f'candidate accounting sums to {acct.total}, archive is {len(archive)} bytes')
        return acct

    def pack(self, index_width):
        if index_width is None:
            if 'archive_compact_index' not in self.result:
                return None, None
            arc = bytes(self.result['archive_compact_index'])
            return arc, self._acct(self.result['accounting_compact_index'], arc)
        return self.archive, self._acct(self.result['accounting'], self.archive)

    def lane_form_bytes(self):
        return self.result.get('like_for_like_bytes')

    def stored_bytes(self) -> int:
        a = self.result['accounting']
        return int(a['framing']) + int(a['payload'])

    def model_bytes(self) -> int:
        return int(self.result['accounting']['model'])


class NativeCandidateReader:
    def __init__(self, spec: dict, archive: bytes):
        self.lib = ctypes.CDLL(str(spec['library']))
        self._open = getattr(self.lib, spec['open'])
        self._decode = getattr(self.lib, spec['decode'])
        self._close = getattr(self.lib, spec['close']) if spec.get('close') else None
        self._open.restype = ctypes.c_void_p
        self._open.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        self._decode.restype = ctypes.c_size_t
        self._decode.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_size_t]
        self._archive = archive   # keep the bytes alive for the lifetime of the context
        self.handle = self._open(archive, len(archive))
        if not self.handle:
            raise RuntimeError('candidate native open() returned NULL')
        self.heap_peak_bytes = None

    def decode(self, i: int, cap: int = 1 << 16) -> bytes:
        buf = ctypes.create_string_buffer(cap + 64)
        n = self._decode(self.handle, i, buf, cap)
        if n == FB_ERR:
            raise RuntimeError(f'candidate native decode failed for record {i}')
        return buf.raw[:n]

    @property
    def decode_fn_addr(self) -> int:
        return ctypes.cast(self._decode, ctypes.c_void_p).value

    def close(self) -> None:
        if self.handle and self._close is not None:
            self._close.argtypes = [ctypes.c_void_p]
            self._close(self.handle)
        self.handle = None


class CandidateAdapter(Codec):
    def __init__(self, cand):
        self.cand = cand
        self.name = getattr(cand, 'name', type(cand).__name__)
        self.label = getattr(cand, 'label', 'candidate codec')
        self.table = 'per-record'
        self.is_candidate = True
        self._train_groups = None

    def train(self, train: Sequence[bytes], ctx) -> dict:
        report = self.cand.train(list(train), ctx.groups)
        return {'selection': 'candidate-defined', **(report or {})}

    def encode(self, records, groups=None):
        return OpaqueEncoded(self.cand.encode(list(records), groups))

    def open_reader(self, native, archive):
        return self.cand.open(archive)

    def native_reader(self, archive: bytes):
        spec = self.cand.native_decoder() if hasattr(self.cand, 'native_decoder') else None
        return NativeCandidateReader(spec, archive) if spec else None


def load_candidate(spec: str) -> CandidateAdapter:
    """spec is `path/to/file.py:ClassName`."""
    path, _, cls_name = spec.rpartition(':')
    if not path or not cls_name:
        raise ValueError('candidate must be given as path/to/file.py:ClassName')
    p = Path(path).resolve()
    mod_spec = importlib.util.spec_from_file_location(f'fb_candidate_{p.stem}', p)
    if mod_spec is None or mod_spec.loader is None:
        raise ValueError(f'cannot import candidate file {p.name}')
    mod = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(mod)
    return CandidateAdapter(getattr(mod, cls_name)())
