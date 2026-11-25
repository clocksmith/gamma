# UNFINISHED. Part of a short-record-decision freeze that was paused before FREEZE.json was written.
# Nothing here is pinned. See ../FREEZE-PROGRESS.md for what was run, what was never run, and the next steps.
"""Shared helpers for the freeze tools of `short-record-decision-v1`.

Loads custody record files, sets up imports of the baseline harness, and builds baseline
codecs with fixed settings. A fixed-setting codec is the harness's own codec class with only
`train` replaced: it fits the one given setting on the whole training input with the harness's
own fitting function, instead of searching for a setting. Encoding, the container, byte
accounting, verification and timing are the harness's code, unchanged.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent


def _literals_dir(start: Path) -> Path:
    """The `literals/` directory, found by walking up from this file."""
    for p in (start, *start.parents):
        if (p / 'fair-baselines-v1').is_dir() and (p / 'rung2-short-ra-bench-v1').is_dir():
            return p
    raise RuntimeError('cannot find the literals directory above this file')


LITERALS = _literals_dir(HERE)
HARNESS_DIR = LITERALS / 'fair-baselines-v1'
if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

import fb_codecs as K  # noqa: E402
import fb_core as C  # noqa: E402
import fb_native as N  # noqa: E402

# Every harness file that takes part in fitting, encoding, accounting, verifying or timing.
HARNESS_FILES = (
    'fair-baselines-v1/fb_candidate.py',
    'fair-baselines-v1/fb_codecs.py',
    'fair-baselines-v1/fb_core.py',
    'fair-baselines-v1/fb_measure.py',
    'fair-baselines-v1/fb_native.py',
    'fair-baselines-v1/native/fb_native.c',
    'fair-baselines-v1/native/fb_native.h',
    'fair-baselines-v1/native/fb_fsst_shim.cpp',
)
# Reference FSST sources compiled into the helper (cwida/fsst).
FSST_FILES = ('fsst.h', 'libfsst.cpp', 'libfsst.hpp', 'fsst_avx512.cpp')

WORKLOADS = ('w1-short-files', 'w2-message-entries', 'w3-commit-subjects')
ZSTD_METHODS = {
    # method name -> (framing, records per block)
    'zstd-lean-frame-tuned': ('lean-frame', 1),
    'zstd-raw-block-tuned': ('raw-block', 1),
    'zstd-lean-frame-blocks-of-2': ('lean-frame', 2),
    'zstd-lean-frame-blocks-of-4': ('lean-frame', 4),
    'zstd-lean-frame-blocks-of-8': ('lean-frame', 8),
    'zstd-lean-frame-blocks-of-16': ('lean-frame', 16),
}
SETTING_KEYS = ('level', 'dict_kind', 'dict_bytes_requested')


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def file_hashes(rel_paths, root: Path = LITERALS) -> dict[str, str]:
    return {rel: sha256_file(root / rel) for rel in rel_paths}


def load_custody_jsonl(path) -> tuple[list[bytes], list[str]]:
    """Records and their source labels from a custody record file: one JSON object per line with
    `id`, `source` and `record_b64`. Order is the file's order."""
    records, sources = [], []
    with open(path, 'r', encoding='utf-8') as fh:
        for ln, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if 'record_b64' not in obj:
                raise ValueError(f'line {ln}: no record_b64 field')
            records.append(base64.b64decode(obj['record_b64'], validate=True))
            sources.append(str(obj.get('source', '')))
    if not records:
        raise ValueError('no records in the input')
    return records, sources


def record_set(records) -> C.RecordSet:
    """No group labels: the splits are by source, so a test source never has a training group."""
    return C.RecordSet(list(records), None, 'custody-jsonl')


def load_native(fsst_src=None, build_dir=None) -> N.Native:
    fsst = Path(fsst_src) if fsst_src else N.default_fsst_src()
    return N.load_native(fsst, Path(build_dir) if build_dir else None)


def model_sha256(data: bytes) -> str:
    return hashlib.sha256(bytes(data)).hexdigest()


# ---------------------------------------------------------------- fixed-setting baseline codecs

class PinnedZstd(K.ZstdTunedCodec):
    """Harness zstd codec with one fixed setting."""

    def __init__(self, native, framing: str, per_block: int, setting: dict):
        super().__init__(native, framing, per_block)
        self.setting = {k: setting[k] for k in SETTING_KEYS}
        self.label = self.label.replace('tuned on training input', 'setting fixed in FREEZE.json')

    def train(self, train, ctx):
        if self.framing == 'raw-block' and any(len(r) > K.ZSTD_BLOCK_MAX for r in train):
            raise K.NotApplicable('a record is larger than one zstd block (128 KiB)')
        model = self._fit(ctx, 'all', list(train), self.setting)
        if model is None:
            raise K.NotApplicable('the fixed dictionary setting could not be trained on the training input')
        self.cfg, (self.dict_bytes, self.dict_is_raw) = dict(self.setting), model
        return {'selection': 'fixed in FREEZE.json',
                'chosen': {**self.cfg, 'dict_bytes_actual': len(self.dict_bytes), 'model_sha256': model_sha256(self.dict_bytes)}}


class PinnedDeflate(K.DeflateTunedCodec):
    """Harness raw-DEFLATE codec with one fixed setting."""

    def __init__(self, native, setting: dict):
        super().__init__(native)
        self.setting = {k: setting[k] for k in SETTING_KEYS}
        self.label = self.label.replace('tuned on training input', 'setting fixed in FREEZE.json')

    def train(self, train, ctx):
        model = self._fit(ctx, 'all', list(train), self.setting)
        if model is None:
            raise K.NotApplicable('the fixed dictionary setting could not be built on the training input')
        self.cfg, self.zdict = dict(self.setting), model
        return {'selection': 'fixed in FREEZE.json',
                'chosen': {**self.cfg, 'mem_level': 9, 'dict_bytes_actual': len(self.zdict), 'model_sha256': model_sha256(self.zdict)}}


class HashedFsst(K.FsstReferenceCodec):
    """Reference FSST as the harness runs it; the report also carries the table's hash."""

    def train(self, train, ctx):
        rep = super().train(train, ctx)
        rep['chosen']['model_sha256'] = model_sha256(self.table_bytes)
        return rep


def pinned_baseline_factory(native, name: str, setting: dict | None):
    """Factory for one baseline by its harness method name."""
    if name == 'raw-indexed':
        return K.RawCodec
    if name in ZSTD_METHODS:
        framing, per_block = ZSTD_METHODS[name]
        return lambda: PinnedZstd(native, framing, per_block, setting)
    if name == 'deflate-raw-tuned':
        return lambda: PinnedDeflate(native, setting)
    if name == 'fsst-reference':
        return lambda: HashedFsst(native)
    raise ValueError(f'no fixed-setting codec for method {name!r}')


def utc_now() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def scrub_env_for_scoring() -> None:
    """A scoring run trains from the training records; it never reads a model cache."""
    os.environ.pop('BITS_ADAPTER_CACHE_DIR', None)
