"""Baseline codecs and their training-only tuning.

Every codec follows the same three steps:

  train(train_records, ctx)   choose settings and fit the model, using training records only
  encode(records)             -> EncodedUnits (model + one stored unit per record or per block)
  reader over the archive     any single record decodes on its own

Tuned baselines choose their settings by k-fold cross-validation inside the training input:
fit on k-1 folds, measure stored bytes on the held-out fold, sum over folds. Each training record
is validated exactly once, so the sum estimates the stored bytes of an archive holding as many
unseen records as the training input. The dictionary is charged once. The final model is then
refit on the whole training input with the chosen settings. Test records are never consulted.

The two "lane-rule" baselines instead reproduce the selection rule of
`../rung2-short-ra-bench-v1/run_ra_pareto_bench.py` so its committed numbers can be checked.
"""
from __future__ import annotations

import random
import struct
import sys
import time
import zlib
from pathlib import Path
from typing import Callable, Sequence

sys.dont_write_bytecode = True   # lane code is imported from a sibling directory; leave no cache files there

import fb_core as C  # noqa: E402
import fb_native as N  # noqa: E402

HERE = Path(__file__).resolve().parent
LANE_BENCH_DIR = HERE.parent / 'rung2-short-ra-bench-v1'

DICT_SIZES = [256, 512, 768, 1024, 1536, 2048, 3072, 4096, 6144, 8192, 12288, 16384, 32768, 65536, 112640]
GRIDS = {
    'full': {'zstd_levels': [1, 3, 9, 15, 19, 22], 'zstd_kinds': ['fastcover', 'cover', 'raw-sample'],
             'deflate_levels': [6, 9], 'sizes': DICT_SIZES,
             'deflate_kinds': ['zstd-fastcover-full', 'zstd-fastcover-content', 'zstd-cover-content', 'raw-sample']},
    'quick': {'zstd_levels': [3, 19], 'zstd_kinds': ['fastcover', 'raw-sample'],
              'deflate_levels': [9], 'sizes': [1024, 2048, 4096, 8192],
              'deflate_kinds': ['zstd-fastcover-full', 'zstd-fastcover-content', 'raw-sample']},
}
ZSTD_BLOCK_MAX = 1 << 17
LANE_DICT_SIZES = (1024, 2048, 4096, 8192)
LANE_ZSTD_LEVEL = 19
LANE_DICT_TRAIN_LEVEL = 3   # the zstd CLI default for `--train`


class NotApplicable(RuntimeError):
    """The method cannot be used on this input; reported, not counted as a failure."""


# ---------------------------------------------------------------- tuning context

def make_folds(n: int, k: int, seed: int) -> list[tuple[list[int], list[int]]]:
    """Seeded k-fold split. Returns (fit indexes, validation indexes), both in original order."""
    k = min(k, n)
    if k < 2:
        return []
    perm = list(range(n))
    random.Random(seed).shuffle(perm)
    folds = []
    for j in range(k):
        val = sorted(perm[j::k])
        val_set = set(val)
        folds.append(([i for i in range(n) if i not in val_set], val))
    return folds


def zstd_cli_sample_order(records: Sequence[bytes]) -> list[bytes]:
    """The order in which `zstd --train` (1.5.x) feeds sample files to the trainer: a fixed-seed
    shuffle of the command-line order. fastCover trains on the first 75% of the samples and scores
    on the rest, so on input that is sorted by kind the order changes the dictionary. With this
    order the helper's dictionaries are byte-identical to the CLI's (checked in the unit tests when
    the CLI is installed)."""
    items = list(records)
    seed, mask = 0xFD2FB528, 0xFFFFFFFF
    for i in range(len(items) - 1, 0, -1):
        seed = ((seed * 2654435761) & mask) ^ 2246822519
        seed = ((seed << 13) | (seed >> 19)) & mask
        j = (seed >> 5) % (i + 1)
        items[i], items[j] = items[j], items[i]
    return items


def raw_sample_dict(records: Sequence[bytes], size: int) -> bytes:
    """Whole records taken at an even stride, concatenated in order, last `size` bytes kept."""
    total = sum(len(r) for r in records)
    stride = max(1, total // max(size, 1))
    return b''.join(records[::stride])[-size:]


class TuneContext:
    def __init__(self, native: N.Native, train: Sequence[bytes], *, folds: int = 4, seed: int = 1,
                 grid: str = 'full', groups: Sequence[str] | None = None):
        self.native = native
        self.train = list(train)
        self.groups = list(groups) if groups is not None else None
        self.k, self.seed, self.grid_name = folds, seed, grid
        self.grid = GRIDS[grid]
        self.folds = make_folds(len(self.train), folds, seed)
        self._dicts: dict[tuple, bytes | None] = {}
        self._dict_sec: dict[tuple, float] = {}
        self._subs: dict[tuple, 'TuneContext'] = {}
        self.reused_sec = 0.0

    def fit_sets(self):
        for j, (fit, val) in enumerate(self.folds):
            yield j, [self.train[i] for i in fit], [self.train[i] for i in val]

    def min_fit_bytes(self) -> int:
        if not self.folds:
            return sum(len(r) for r in self.train)
        return min(sum(len(self.train[i]) for i in fit) for fit, _ in self.folds)

    def zdict(self, fold_id, records: Sequence[bytes], kind: str, size: int, level: int) -> bytes | None:
        """zstd-trained dictionary, cached. None when zstd cannot train one from these records.

        The cache is shared by the codecs measured in one run. When a codec reuses a dictionary
        another codec already trained, the original training time is added to `reused_sec`, so a
        codec's reported build cost does not depend on the order the codecs were run in."""
        key = (fold_id, kind, size, level)
        if key in self._dicts:
            self.reused_sec += self._dict_sec[key]
        else:
            t0 = time.perf_counter()
            try:
                self._dicts[key] = self.native.zdict_train(
                    N.ZDICT_FASTCOVER if kind == 'fastcover' else N.ZDICT_COVER,
                    zstd_cli_sample_order(records), size, level)
            except N.NativeError:
                self._dicts[key] = None
            self._dict_sec[key] = time.perf_counter() - t0
        return self._dicts[key]

    def sub(self, indexes: Sequence[int]) -> 'TuneContext':
        key = tuple(indexes)
        if key not in self._subs:
            self._subs[key] = TuneContext(self.native, [self.train[i] for i in indexes], folds=self.k,
                                          seed=self.seed, grid=self.grid_name)
        return self._subs[key]

    def take_reused_sec(self) -> float:
        total = self.reused_sec + sum(s.take_reused_sec() for s in self._subs.values())
        self.reused_sec = 0.0
        return total

    def describe(self) -> dict:
        return {'folds': len(self.folds), 'fold_seed': self.seed, 'grid': self.grid_name,
                'fold_sizes': [len(v) for _, v in self.folds]}


def _cv_select(ctx: TuneContext, configs: list[dict], fit_model: Callable, stored_bytes: Callable) -> dict:
    """Generic selection. fit_model(fold_id, fit_records, cfg) -> model or None;
    stored_bytes(model, records, cfg) -> stored bytes (index excluded)."""
    if not ctx.folds:
        raise NotApplicable('too few training records to hold out a validation part')
    stored = [0] * len(configs)
    model_sizes: list[list[int]] = [[] for _ in configs]
    valid = [True] * len(configs)
    for fold_id, fit, val in ctx.fit_sets():
        for ci, cfg in enumerate(configs):
            if not valid[ci]:
                continue
            model = fit_model(fold_id, fit, cfg)
            if model is None:
                valid[ci] = False
                continue
            stored[ci] += stored_bytes(model, val, cfg)
            model_sizes[ci].append(_model_len(model))
    scored = []
    for ci, cfg in enumerate(configs):
        if not valid[ci]:
            continue
        mean_model = sum(model_sizes[ci]) / len(model_sizes[ci])
        scored.append((mean_model + stored[ci], mean_model, ci))
    if not scored:
        raise NotApplicable('no setting could be fitted on the training input')
    scored.sort()
    return {
        'selection': 'k-fold cross-validation inside the training input',
        'objective': 'mean fold model bytes + stored bytes summed over validation folds (index excluded; it is the same for every setting)',
        **ctx.describe(),
        'settings_evaluated': len(scored),
        'settings_skipped': len(configs) - len(scored),
        'ranked': [{'estimate_bytes': round(est, 1), 'mean_model_bytes': round(mm, 1), **configs[ci]}
                   for est, mm, ci in scored],
    }


def _model_len(model) -> int:
    return len(model[0]) if isinstance(model, tuple) else len(model)


def _finalize(report: dict, configs_key: str = 'ranked', keep: int = 5) -> dict:
    out = dict(report)
    out['best_5'] = out.pop(configs_key)[:keep]
    return out


# ---------------------------------------------------------------- base class

class Codec:
    name = ''
    label = ''
    table = 'per-record'   # or 'blocks'
    tuned = False

    def train(self, train: Sequence[bytes], ctx: TuneContext) -> dict:
        return {'selection': 'none (no settings)'}

    def encode(self, records: Sequence[bytes], groups: Sequence[str] | None = None) -> C.EncodedUnits:
        raise NotImplementedError

    def open_reader(self, native: N.Native, archive: bytes):
        return native.open(archive)


class RawCodec(Codec):
    name = 'raw-indexed'
    label = 'uncompressed records plus index'

    def encode(self, records, groups=None):
        return C.EncodedUnits(C.M_RAW, C.MODEL_NONE, b'', list(records), [0] * len(records), len(records))


# ---------------------------------------------------------------- zstd

_ZSTD_MODES = {
    'frame': (N.ZSTD_MODE_FRAME, C.M_ZSTD_FRAME),
    'lean-frame': (N.ZSTD_MODE_LEAN_FRAME, C.M_ZSTD_LEAN_FRAME),
    'raw-block': (N.ZSTD_MODE_BLOCK, C.M_ZSTD_BLOCK),
}


def _zstd_units(native: N.Native, records: Sequence[bytes], *, dict_bytes: bytes, dict_is_raw: bool, level: int,
                framing: str, per_block: int = 1) -> C.EncodedUnits:
    mode, method = _ZSTD_MODES[framing]
    n = len(records)
    model_kind = C.MODEL_NONE if not dict_bytes else (C.MODEL_ZSTD_RAW if dict_is_raw else C.MODEL_ZSTD_DICT)
    if per_block > 1:
        blocks = [b''.join(records[i:i + per_block]) for i in range(0, n, per_block)]
        frames = native.zstd_encode_many(blocks, dict_bytes=dict_bytes, dict_is_raw=dict_is_raw, level=level,
                                         mode=N.ZSTD_MODE_LEAN_FRAME)
        framing_bytes = [sum(native.zstd_frame_account(f, True)[:3]) for f in frames]
        ends, cur = [], 0
        for r in records:
            cur += len(r)
            ends.append(cur)
        return C.EncodedUnits(C.M_ZSTD_LEAN_GROUP, model_kind, dict_bytes, frames, framing_bytes, n,
                              per_block=per_block, rec_raw_ends=ends,
                              detail={'blocks': len(frames), 'frame_format': 'magicless, no content size, no checksum, no dictionary ID'})
    outs = native.zstd_encode_many(records, dict_bytes=dict_bytes, dict_is_raw=dict_is_raw, level=level, mode=mode)
    if framing == 'raw-block':
        flags = bytearray((n + 7) // 8)
        units = []
        for i, (rec, out) in enumerate(zip(records, outs)):
            if out:
                units.append(out)
            else:   # zstd declined to compress this block; keep the record as is and flag it
                units.append(rec)
                flags[i >> 3] |= 1 << (i & 7)
        stored_raw = sum(bin(b).count('1') for b in flags)
        return C.EncodedUnits(method, model_kind, dict_bytes, units, [0] * n, n, aux=bytes(flags),
                              detail={'records_stored_raw': stored_raw, 'flag_bitmap_bytes': len(flags)})
    acct = [native.zstd_frame_account(f, framing == 'lean-frame') for f in outs]
    detail = {
        'frame_header_bytes': sum(a[0] for a in acct),
        'block_header_bytes': sum(a[1] for a in acct),
        'checksum_bytes': sum(a[2] for a in acct),
        'framing_bytes_per_record_min_max': [min((sum(a[:3]) for a in acct), default=0),
                                             max((sum(a[:3]) for a in acct), default=0)],
    }
    return C.EncodedUnits(method, model_kind, dict_bytes, outs, [sum(a[:3]) for a in acct], n, detail=detail)


class ZstdTunedCodec(Codec):
    tuned = True

    def __init__(self, native: N.Native, framing: str, per_block: int = 1):
        self.native, self.framing, self.per_block = native, framing, per_block
        if per_block > 1:
            self.name = f'zstd-lean-frame-blocks-of-{per_block}'
            self.label = f'zstd, one lean frame per block of {per_block} records, tuned on training input'
            self.table = 'blocks'
        else:
            self.name = f'zstd-{framing}-tuned'
            self.label = {
                'frame': 'zstd per record, standard frame without checksum, tuned on training input',
                'lean-frame': 'zstd per record, magicless frame, no content size, no checksum, no dictionary ID, tuned on training input',
                'raw-block': 'zstd per record, raw block with preloaded dictionary and no frame, tuned on training input',
            }[framing]
        self.cfg: dict | None = None
        self.dict_bytes = b''
        self.dict_is_raw = False

    def _fit(self, ctx: TuneContext, fold_id, records, cfg):
        kind = cfg['dict_kind']
        if kind == 'none':
            return (b'', False)
        if kind == 'raw-sample':
            return (raw_sample_dict(records, cfg['dict_bytes_requested']), True)
        d = ctx.zdict(fold_id, records, kind, cfg['dict_bytes_requested'], cfg['level'])
        return None if d is None else (d, False)

    def _stored(self, model, records, cfg) -> int:
        return _zstd_units(self.native, records, dict_bytes=model[0], dict_is_raw=model[1], level=cfg['level'],
                           framing=self.framing, per_block=self.per_block).stored_bytes()

    def train(self, train, ctx):
        if self.framing == 'raw-block' and any(len(r) > ZSTD_BLOCK_MAX for r in train):
            raise NotApplicable('a record is larger than one zstd block (128 KiB)')
        g = ctx.grid
        sizes = [s for s in g['sizes'] if s <= ctx.min_fit_bytes()]
        configs = [{'level': lv, 'dict_kind': 'none', 'dict_bytes_requested': 0} for lv in g['zstd_levels']]
        configs += [{'level': lv, 'dict_kind': k, 'dict_bytes_requested': s}
                    for k in g['zstd_kinds'] for s in sizes for lv in g['zstd_levels']]
        report = _cv_select(ctx, configs, lambda f, r, c: self._fit(ctx, f, r, c), self._stored)
        for cand in report['ranked']:
            cfg = {k: cand[k] for k in ('level', 'dict_kind', 'dict_bytes_requested')}
            model = self._fit(ctx, 'all', list(train), cfg)
            if model is not None:
                self.cfg, (self.dict_bytes, self.dict_is_raw) = cfg, model
                break
        else:
            raise NotApplicable('no dictionary could be trained on the full training input')
        report['chosen'] = {**self.cfg, 'dict_bytes_actual': len(self.dict_bytes)}
        return _finalize(report)

    def encode(self, records, groups=None):
        if self.framing == 'raw-block' and any(len(r) > ZSTD_BLOCK_MAX for r in records):
            raise NotApplicable('a record is larger than one zstd block (128 KiB)')
        return _zstd_units(self.native, list(records), dict_bytes=self.dict_bytes, dict_is_raw=self.dict_is_raw,
                           level=self.cfg['level'], framing=self.framing, per_block=self.per_block)


def _lane_trained_dicts(ctx: TuneContext, train: Sequence[bytes]) -> list[tuple[int, bytes]]:
    out = [(0, b'')]
    for md in LANE_DICT_SIZES:
        d = ctx.zdict('all', train, 'fastcover', md, LANE_DICT_TRAIN_LEVEL)
        if d is not None:
            out.append((md, d))
    return out


class ZstdLaneRuleCodec(Codec):
    name = 'zstd-frame-lane-rule'
    label = ('zstd -19 per record, standard frame without checksum; dictionary from `zstd --train` defaults, '
             'size picked from {0,1,2,4,8} KiB by smallest archive of the TRAINING records (the lane\'s rule)')

    def __init__(self, native: N.Native):
        self.native = native
        self.dict_bytes = b''
        self.maxdict = 0

    def _units(self, records, d):
        return _zstd_units(self.native, list(records), dict_bytes=d, dict_is_raw=False, level=LANE_ZSTD_LEVEL,
                           framing='frame')

    def train(self, train, ctx):
        cands = []
        for md, d in _lane_trained_dicts(ctx, train):
            cands.append((self._units(train, d).lane_form_bytes(), md, d))
        cands.sort(key=lambda x: x[0])
        in_sample, self.maxdict, self.dict_bytes = cands[0]
        return {'selection': 'in-sample on the training records (the lane\'s rule, reproduced)',
                'chosen': {'level': LANE_ZSTD_LEVEL, 'maxdict': self.maxdict, 'dict_bytes_actual': len(self.dict_bytes)},
                'in_sample_lane_form_bytes': in_sample,
                'candidates': [{'maxdict': md, 'in_sample_lane_form_bytes': b} for b, md, _ in cands]}

    def encode(self, records, groups=None):
        return self._units(records, self.dict_bytes)


# ---------------------------------------------------------------- DEFLATE

def _deflate_one(rec: bytes, level: int, zdict: bytes | None) -> bytes:
    if zdict is None:
        co = zlib.compressobj(level, zlib.DEFLATED, -15, 9)
    else:
        co = zlib.compressobj(level, zlib.DEFLATED, -15, 9, zlib.Z_DEFAULT_STRATEGY, zdict)
    return co.compress(rec) + co.flush(zlib.Z_FINISH)


def _deflate_units(records: Sequence[bytes], level: int, zdict: bytes, always_pass_dict: bool = False) -> C.EncodedUnits:
    zd = zdict if (zdict or always_pass_dict) else None
    units = [_deflate_one(r, level, zd) for r in records]
    return C.EncodedUnits(C.M_DEFLATE, C.MODEL_DEFLATE_DICT if zdict else C.MODEL_NONE, zdict, units,
                          [0] * len(units), len(units),
                          detail={'note': 'the 3-bit block header, end-of-block code and bit padding are inside the payload bytes'})


class DeflateTunedCodec(Codec):
    name = 'deflate-raw-tuned'
    label = 'raw DEFLATE (wbits -15) per record with preset dictionary, tuned on training input'
    tuned = True

    def __init__(self, native: N.Native):
        self.native = native
        self.cfg: dict | None = None
        self.zdict = b''

    def _fit(self, ctx, fold_id, records, cfg):
        kind, size = cfg['dict_kind'], cfg['dict_bytes_requested']
        if kind == 'none':
            return b''
        if kind == 'raw-sample':
            return raw_sample_dict(records, size)
        trainer = 'fastcover' if 'fastcover' in kind else 'cover'
        d = ctx.zdict(fold_id, records, trainer, size, LANE_DICT_TRAIN_LEVEL)
        if d is None:
            return None
        if kind.endswith('-content'):
            d = d[self.native.zdict_header_size(d):]
        return d[-32768:]

    def train(self, train, ctx):
        g = ctx.grid
        sizes = [s for s in g['sizes'] if s <= min(32768, ctx.min_fit_bytes())]
        configs = [{'level': lv, 'dict_kind': 'none', 'dict_bytes_requested': 0} for lv in g['deflate_levels']]
        configs += [{'level': lv, 'dict_kind': k, 'dict_bytes_requested': s}
                    for k in g['deflate_kinds'] for s in sizes for lv in g['deflate_levels']]
        report = _cv_select(ctx, configs, lambda f, r, c: self._fit(ctx, f, r, c),
                            lambda m, recs, c: _deflate_units(recs, c['level'], m).stored_bytes())
        for cand in report['ranked']:
            cfg = {k: cand[k] for k in ('level', 'dict_kind', 'dict_bytes_requested')}
            model = self._fit(ctx, 'all', list(train), cfg)
            if model is not None:
                self.cfg, self.zdict = cfg, model
                break
        else:
            raise NotApplicable('no dictionary could be built on the full training input')
        report['chosen'] = {**self.cfg, 'mem_level': 9, 'dict_bytes_actual': len(self.zdict)}
        return _finalize(report)

    def encode(self, records, groups=None):
        return _deflate_units(list(records), self.cfg['level'], self.zdict)


class DeflateLaneRuleCodec(Codec):
    name = 'deflate-raw-lane-rule'
    label = ('raw DEFLATE level 9 per record; preset dictionary picked from zstd-trained dictionaries and raw '
             'corpus tails of {1,2,4,8} KiB by smallest archive of the TRAINING records (the lane\'s rule)')

    def __init__(self, native: N.Native):
        self.native = native
        self.zdict = b''
        self.kind = ''

    def train(self, train, ctx):
        train = list(train)
        cands = []
        for md, d in _lane_trained_dicts(ctx, train):
            cands.append((_deflate_units(train, 9, d, True).lane_form_bytes(), f'zdict_{md}', d))
        raw_concat = b''.join(train[::max(1, len(train) // 64)])
        for raw_sz in LANE_DICT_SIZES:
            rd = raw_concat[-raw_sz:] if len(raw_concat) >= raw_sz else raw_concat
            cands.append((_deflate_units(train, 9, rd, True).lane_form_bytes(), f'raw_{raw_sz}', rd))
        cands.sort(key=lambda x: x[0])
        in_sample, self.kind, self.zdict = cands[0]
        return {'selection': 'in-sample on the training records (the lane\'s rule, reproduced)',
                'chosen': {'level': 9, 'mem_level': 9, 'dict_kind': self.kind, 'dict_bytes_actual': len(self.zdict)},
                'in_sample_lane_form_bytes': in_sample,
                'candidates': [{'dict_kind': k, 'in_sample_lane_form_bytes': b} for b, k, _ in cands]}

    def encode(self, records, groups=None):
        return _deflate_units(list(records), 9, self.zdict, True)


# ---------------------------------------------------------------- FSST

class FsstReferenceCodec(Codec):
    name = 'fsst-reference'
    label = 'FSST reference implementation (cwida/fsst), symbol table built from the training input'

    def __init__(self, native: N.Native):
        if not native.has_fsst:
            raise NotApplicable('the reference FSST sources were not available when the helper was built')
        self.native = native
        self.encoder = None
        self.table_bytes = b''

    def train(self, train, ctx):
        self.encoder = self.native.fsst_train(list(train))
        self.table_bytes = self.encoder.export()
        return {'selection': 'none (the reference library exposes no tuning settings)',
                'chosen': {'exported_table_bytes': len(self.table_bytes)}}

    def encode(self, records, groups=None):
        units = self.encoder.compress(list(records))
        return C.EncodedUnits(C.M_FSST, C.MODEL_FSST_TABLE, self.table_bytes, units, [0] * len(units), len(units),
                              detail={'model_serialization': 'fsst_export()'})


class LaneFsstReader:
    """Python reader for the lane's own FSST-255 symbol format stored in this harness's container."""

    def __init__(self, archive: bytes):
        if archive[:4] != C.MAGIC or archive[4] != C.M_LANE_FSST:
            raise ValueError('not a lane-FSST archive')
        w = archive[5]
        self.count, model_len = struct.unpack_from('<II', archive, 8)
        pos = C.HEADER_BYTES
        (nsym,) = struct.unpack_from('<H', archive, pos)
        lens = archive[pos + 2:pos + 2 + nsym]
        sp = pos + 2 + nsym
        self.symbols = []
        for ln in lens:
            self.symbols.append(archive[sp:sp + ln])
            sp += ln
        pos += model_len
        self.ends = [int.from_bytes(archive[pos + i * w:pos + (i + 1) * w], 'little') for i in range(self.count)]
        self.body = archive[pos + self.count * w:]
        if self.ends and self.ends[-1] != len(self.body):
            raise ValueError('index does not cover the stored bytes')

    def decode(self, i: int, cap: int = 0) -> bytes:
        s = self.ends[i - 1] if i else 0
        data, out, p = self.body[s:self.ends[i]], bytearray(), 0
        while p < len(data):
            code = data[p]
            if code == 255:
                out.append(data[p + 1])
                p += 2
            else:
                out += self.symbols[code]
                p += 1
        return bytes(out)

    def close(self) -> None:
        pass


class FsstLaneImplCodec(Codec):
    name = 'fsst-lane-own-impl'
    label = "FSST-255 as implemented by the lane itself (fsst255_codec.py); not the reference implementation"

    def __init__(self):
        if not (LANE_BENCH_DIR / 'fsst255_codec.py').is_file():
            raise NotApplicable('the lane\'s fsst255_codec.py is not present')
        if str(LANE_BENCH_DIR) not in sys.path:
            sys.path.insert(0, str(LANE_BENCH_DIR))
        import fsst255_codec  # noqa: E402  (the lane's baseline code, not its BIT3 codec)
        self.mod = fsst255_codec
        self.symbols: list[bytes] = []

    def train(self, train, ctx):
        self.symbols = self.mod.train_fsst255_table(list(train))
        return {'selection': 'none (the lane\'s trainer, called as its benchmark calls it)',
                'chosen': {'symbols': len(self.symbols)}}

    def encode(self, records, groups=None):
        if len(records) > 0xFFFF:
            raise NotApplicable('the lane\'s FSST container holds at most 65,535 records')
        blob = self.mod.serialize_fsst255_archive(self.symbols, list(records))
        nsym, ndocs = struct.unpack_from('<HH', blob, 4)
        table_len = nsym + sum(blob[8:8 + nsym])
        model = struct.pack('<H', nsym) + blob[8:8 + table_len]
        pos = 8 + table_len
        ends = struct.unpack_from(f'<{ndocs}I', blob, pos)
        body = blob[pos + 4 * ndocs:]
        units = [body[(ends[i - 1] if i else 0):ends[i]] for i in range(ndocs)]
        return C.EncodedUnits(C.M_LANE_FSST, C.MODEL_LANE_FSST_TABLE, model, units, [0] * ndocs, ndocs,
                              detail={'lane_form_bytes_exact': len(blob),
                                      'note': 'lane_form_bytes_exact is the length of the blob the lane\'s serializer returns'})

    def open_reader(self, native, archive):
        return LaneFsstReader(archive)


# ---------------------------------------------------------------- partitioned (one model per group)

class PartitionedCodec(Codec):
    """One independently trained sub-codec per record group. Records of a group must be contiguous.
    This gives a baseline the same side information the lane's two-table BIT3 layout uses: which of
    the known groups a record belongs to, taken from its position."""
    tuned = True

    def __init__(self, factory: Callable[[], Codec]):
        self.factory = factory
        probe = factory()
        self.name = probe.name + '/per-group'
        self.label = probe.label + '; one model per record group'
        self.table = probe.table
        self.subs: dict[str, Codec] = {}

    def train(self, train, ctx):
        if ctx.groups is None:
            raise NotApplicable('the training input has no group labels')
        labels = sorted(set(ctx.groups))
        if len(labels) < 2:
            raise NotApplicable('the training input has a single group')
        report = {'selection': 'each group tuned on its own training records', 'groups': {}}
        for g in labels:
            idx = [i for i, lab in enumerate(ctx.groups) if lab == g]
            sub = self.factory()
            report['groups'][g] = sub.train([train[i] for i in idx], ctx.sub(idx))
            self.subs[g] = sub
        return report

    def encode(self, records, groups=None):
        if groups is None:
            raise NotApplicable('the records to encode have no group labels')
        runs: list[tuple[str, int, int]] = []
        for i, g in enumerate(groups):
            if runs and runs[-1][0] == g:
                runs[-1] = (g, runs[-1][1], i + 1)
            else:
                runs.append((g, i, i + 1))
        if len({g for g, _, _ in runs}) != len(runs):
            raise NotApplicable('records of a group are not contiguous')
        parts = []
        for g, s, e in runs:
            if g not in self.subs:
                raise NotApplicable(f'group {g!r} was not in the training input')
            parts.append(self.subs[g].encode(records[s:e]))
        return C.EncodedUnits(C.M_PARTITIONED, C.MODEL_NONE, b'', [], [], len(records), parts=parts,
                              detail={'parts': [{'group': g, 'records': e - s} for g, s, e in runs]})


# ---------------------------------------------------------------- registry

def build_baselines(native: N.Native, *, block_sizes: Sequence[int] = (2, 4, 8, 16), per_group: bool = True,
                    only: Sequence[str] | None = None) -> list[tuple[str, Callable[[], Codec]]]:
    """(name, factory) for every baseline, in report order. Factories may raise NotApplicable."""
    items: list[tuple[str, Callable[[], Codec]]] = [
        ('raw-indexed', RawCodec),
        ('zstd-frame-lane-rule', lambda: ZstdLaneRuleCodec(native)),
        ('zstd-frame-tuned', lambda: ZstdTunedCodec(native, 'frame')),
        ('zstd-lean-frame-tuned', lambda: ZstdTunedCodec(native, 'lean-frame')),
        ('zstd-raw-block-tuned', lambda: ZstdTunedCodec(native, 'raw-block')),
        ('deflate-raw-lane-rule', lambda: DeflateLaneRuleCodec(native)),
        ('deflate-raw-tuned', lambda: DeflateTunedCodec(native)),
        ('fsst-reference', lambda: FsstReferenceCodec(native)),
        ('fsst-lane-own-impl', FsstLaneImplCodec),
    ]
    if per_group:
        items += [
            ('zstd-lean-frame-tuned/per-group', lambda: PartitionedCodec(lambda: ZstdTunedCodec(native, 'lean-frame'))),
            ('zstd-raw-block-tuned/per-group', lambda: PartitionedCodec(lambda: ZstdTunedCodec(native, 'raw-block'))),
            ('deflate-raw-tuned/per-group', lambda: PartitionedCodec(lambda: DeflateTunedCodec(native))),
            ('fsst-reference/per-group', lambda: PartitionedCodec(lambda: FsstReferenceCodec(native))),
        ]
    for n in block_sizes:
        items.append((f'zstd-lean-frame-blocks-of-{n}', lambda n=n: ZstdTunedCodec(native, 'lean-frame', per_block=n)))
    if only:
        wanted = set(only)
        unknown = wanted - {name for name, _ in items}
        if unknown:
            raise ValueError(f'unknown method(s): {sorted(unknown)}')
        items = [it for it in items if it[0] in wanted]
    return items
