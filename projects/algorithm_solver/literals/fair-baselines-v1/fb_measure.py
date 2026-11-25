"""Measure every method the same way: build, account, verify, time.

For each method:
  1. train on the training records only (settings are chosen there)
  2. encode the test records
  3. serialize twice: 4 index bytes per offset (the lane's representation) and a compact index
  4. open a reader on the serialized bytes alone and decode every record on its own in a seeded
     random order; any difference from the original marks the method `failed-verification`
  5. time single-record lookups in memory with the one loop in native/fb_native.c
"""
from __future__ import annotations

import platform
import random
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import fb_core as C
import fb_native as N
from fb_candidate import CandidateAdapter
from fb_codecs import Codec, NotApplicable, TuneContext, build_baselines

SCHEMA = 'fair-baselines/v1'


@dataclass
class Options:
    folds: int = 4
    seed: int = 1
    grid: str = 'full'
    lookups: int = 200_000
    rounds: int = 5
    warmup: int = 2_000
    block_sizes: tuple = (2, 4, 8, 16)
    per_group: bool = True
    methods: tuple | None = None
    timing: bool = True


def verify(reader, records: Sequence[bytes], seed: int, cap: int) -> dict:
    n = len(records)
    count = getattr(reader, 'count', n)
    if count != n:
        return {'ok': False, 'records_checked': 0, 'problem': f'reader reports {count} records, expected {n}'}
    order = list(range(n))
    random.Random(seed).shuffle(order)
    for k, i in enumerate(order):
        try:
            got = reader.decode(i, cap)
        except Exception as exc:   # a decode error is a verification failure, not a crash
            return {'ok': False, 'records_checked': k, 'first_bad_record': i, 'problem': f'decode raised {type(exc).__name__}'}
        if got != records[i]:
            return {'ok': False, 'records_checked': k, 'first_bad_record': i, 'problem': 'bytes differ'}
    return {'ok': True, 'records_checked': n,
            'order': 'seeded random permutation; each record decoded on its own from the serialized archive'}


def _python_timing(reader, n: int, lookups: int, seed: int, cap: int) -> dict:
    rng = random.Random(seed)
    idxs = [rng.randrange(n) for _ in range(lookups)]
    samples = []
    pc = time.perf_counter_ns
    for i in idxs:
        a = pc()
        reader.decode(i, cap)
        samples.append(pc() - a)
    samples.sort()
    return {
        'kind': 'python-loop',
        'comparable_with_native': False,
        'note': 'timed in a Python loop; includes interpreter overhead; not comparable with native numbers',
        'lookups': lookups,
        'loop_mean_ns': round(sum(samples) / len(samples), 1),
        'single_lookup_median_ns': N.percentile(samples, 0.50),
        'single_lookup_p95_ns': N.percentile(samples, 0.95),
    }


def _native_timing(native: N.Native, fn_addr: int, ctx_addr: int, n: int, opts: Options, cap: int) -> dict:
    rounds = [native.time_lookups(fn_addr, ctx_addr, n, n_lookups=opts.lookups, warmup=opts.warmup,
                                  seed=0x9E3779B97F4A7C15, out_cap=cap) for _ in range(max(1, opts.rounds))]
    best = min(rounds, key=lambda r: r['loop_mean_ns'])
    return {'kind': 'native-loop', 'comparable_with_native': True, **best,
            'loop_mean_ns_all_rounds': [r['loop_mean_ns'] for r in rounds],
            'reported_round': 'the round with the lowest loop mean (least disturbed by other work on the machine)'}


def _per_lookup_bytes(enc, records: Sequence[bytes]) -> dict | None:
    """Stored bytes read and raw bytes produced to answer one lookup, averaged over records."""
    if not isinstance(enc, C.EncodedUnits):
        return None
    if enc.parts is not None:
        subs, pos = [], 0
        for p in enc.parts:
            subs.append((_per_lookup_bytes(p, records[pos:pos + p.n_records]), p.n_records))
            pos += p.n_records
        n = sum(k for _, k in subs)
        return {
            'mean_stored_bytes_read': round(sum(s['mean_stored_bytes_read'] * k for s, k in subs) / n, 2),
            'mean_raw_bytes_decoded': round(sum(s['mean_raw_bytes_decoded'] * k for s, k in subs) / n, 2),
            'max_raw_bytes_decoded': max(s['max_raw_bytes_decoded'] for s, _ in subs),
        }
    n, pb = enc.n_records, enc.per_block
    stored, raw = [], []
    for b, unit in enumerate(enc.units):
        members = records[b * pb:(b + 1) * pb]
        raw_block = sum(len(r) for r in members)
        stored += [len(unit)] * len(members)
        raw += [raw_block] * len(members)
    return {
        'mean_stored_bytes_read': round(sum(stored) / n, 2) if n else 0,
        'mean_raw_bytes_decoded': round(sum(raw) / n, 2) if n else 0,
        'max_raw_bytes_decoded': max(raw, default=0),
    }


def measure(native: N.Native, name: str, factory, train: C.RecordSet, test: C.RecordSet, ctx: TuneContext,
            opts: Options) -> dict:
    res: dict = {'name': name}
    try:
        codec: Codec = factory()
        res.update(label=codec.label, table=codec.table, tuned_on_training_input=bool(codec.tuned))
        ctx.take_reused_sec()
        t0 = time.perf_counter()
        tuning = codec.train(train.records, ctx)
        t1 = time.perf_counter()
        reused = ctx.take_reused_sec()
        enc = codec.encode(test.records, test.groups)
        t2 = time.perf_counter()
        arc4, acct4 = enc.pack(C.LANE_INDEX_WIDTH)
        arcc, acctc = enc.pack(None)
    except NotApplicable as exc:
        res.update(status='not-applicable', reason=str(exc))
        return res
    except Exception as exc:
        res.update(status='error', reason=f'{type(exc).__name__}: {exc}')
        return res

    res['tuning'] = tuning
    res['build'] = {
        'tune_and_fit_sec': round(t1 - t0 + reused, 4),
        'encode_test_sec': round(t2 - t1, 4),
        'note': 'wall time; tuning includes every cross-validation fit. Build peak memory is not measured.',
    }
    exact = enc.detail.get('lane_form_bytes_exact') if isinstance(enc.detail, dict) else None
    res['bytes'] = {
        'like_for_like_lane_form': exact if exact is not None else enc.lane_form_bytes(),
        'all_in': acct4.as_dict(),
        'all_in_compact_index': acctc.as_dict() if acctc is not None else None,
        'stored_units': enc.stored_bytes(),
        'model': enc.model_bytes(),
    }
    if isinstance(enc, C.EncodedUnits):
        res['detail'] = enc.detail
        res['per_lookup'] = _per_lookup_bytes(enc, test.records)
    else:
        res['detail'] = enc.detail

    cap = max((len(r) for r in test.records), default=0) + 64
    checks = {}
    readers = []
    ok = True
    try:
        for tag, arc in (('index4', arc4), ('compact_index', arcc)):
            if arc is None:
                continue
            rd = codec.open_reader(native, arc)
            readers.append(rd)
            checks[tag] = verify(rd, test.records, opts.seed + 17, cap)
            ok = ok and checks[tag]['ok']
        native_cand = codec.native_reader(arc4) if isinstance(codec, CandidateAdapter) else None
        if native_cand is not None:
            readers.append(native_cand)
            checks['native_decoder'] = verify(native_cand, test.records, opts.seed + 17, cap)
            ok = ok and checks['native_decoder']['ok']
    except Exception as exc:
        checks['problem'] = f'{type(exc).__name__}: {exc}'
        ok = False
    res['verification'] = checks
    if not ok:
        res['status'] = 'failed-verification'
        for rd in readers:
            _close(rd)
        return res
    res['status'] = 'ok'

    main_reader = readers[0]
    timed = native_cand if isinstance(codec, CandidateAdapter) and native_cand is not None else main_reader
    res['memory'] = {
        'archive_bytes': len(arc4),
        'reader_heap_peak_bytes': getattr(timed, 'heap_peak_bytes', None),
        'note': 'reader heap is counted by the helper\'s allocator hooks (contexts, tables, scratch); the archive itself is extra; stack is not counted',
    }
    if opts.timing and len(test.records) > 0:
        try:
            if hasattr(timed, 'decode_fn_addr'):
                res['lookup_timing'] = _native_timing(native, timed.decode_fn_addr, timed.handle, len(test.records), opts, cap)
            else:
                res['lookup_timing'] = _python_timing(timed, len(test.records), min(opts.lookups, 20_000), opts.seed, cap)
        except Exception as exc:
            res['lookup_timing'] = {'kind': 'failed', 'reason': f'{type(exc).__name__}: {exc}'}
    for rd in readers:
        _close(rd)
    return res


def _close(reader) -> None:
    close = getattr(reader, 'close', None)
    if close:
        try:
            close()
        except Exception:
            pass


def _cpu_brand() -> str | None:
    if sys.platform == 'darwin':
        try:
            return subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], capture_output=True, text=True,
                                  timeout=5).stdout.strip() or None
        except Exception:
            return None
    return None


def _load_average() -> float | None:
    try:
        import os
        return round(os.getloadavg()[0], 2)
    except (OSError, AttributeError):
        return None


def fsst_commit(fsst_src: Path | None) -> str | None:
    if not fsst_src or not (Path(fsst_src) / '.git').exists():
        return None
    try:
        out = subprocess.run(['git', '-C', str(fsst_src), 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except Exception:
        return None


def public_arg(arg: str) -> str:
    """Command-line argument as recorded in results: absolute paths are reduced to their last part."""
    if arg.startswith('/'):
        return '<dir>/' + Path(arg).name
    if '=/' in arg:
        key, _, val = arg.partition('=')
        return f'{key}=<dir>/{Path(val).name}'
    return arg


def run(native: N.Native, train: C.RecordSet, test: C.RecordSet, opts: Options, *,
        candidates: Sequence[CandidateAdapter] = (), fsst_src: Path | None = None, command: Sequence[str] | None = None,
        progress=None) -> dict:
    ctx = TuneContext(native, train.records, folds=opts.folds, seed=opts.seed, grid=opts.grid, groups=train.groups)
    items = build_baselines(native, block_sizes=opts.block_sizes, per_group=opts.per_group, only=opts.methods)
    items += [(c.name, (lambda c=c: c)) for c in candidates]
    methods = []
    for name, factory in items:
        t0 = time.perf_counter()
        m = measure(native, name, factory, train, test, ctx, opts)
        methods.append(m)
        if progress:
            total = (m.get('bytes') or {}).get('all_in', {}).get('total')
            progress(f'  {name:38s} {m["status"]:20s} {"" if total is None else total:>9} bytes  ({time.perf_counter() - t0:.1f}s)')
    return {
        'schema': SCHEMA,
        'command': [public_arg(a) for a in command] if command else None,
        'harness': {
            'zstd_library': native.zstd_version,
            'zlib_library': native.zlib_version,
            'reference_fsst_built': native.has_fsst,
            'reference_fsst_commit': fsst_commit(fsst_src) if native.has_fsst else None,
            'native_helper': native.facts,
            'python': platform.python_version(),
            'system': platform.system(),
            'machine': platform.machine(),
            'cpu': _cpu_brand(),
        },
        'timer': {**native.timer_probe(), 'load_average_1m_at_end': _load_average()},
        'options': {**asdict(opts), 'block_sizes': list(opts.block_sizes),
                    'methods': list(opts.methods) if opts.methods else None},
        'inputs': {'train': train.describe(), 'test': test.describe()},
        'methods': methods,
    }
