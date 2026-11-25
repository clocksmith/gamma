#!/usr/bin/env python3
# UNFINISHED. Part of a short-record-decision freeze that was paused before FREEZE.json was written.
# Nothing here is pinned. See ../FREEZE-PROGRESS.md for what was run, what was never run, and the next steps.
"""Score one workload exactly as pinned in FREEZE.json.

    python3 -B score.py run --freeze FREEZE.json --workload w1-short-files \
        --train <custody>/release/w1-short-files/train.jsonl --test <test records>.jsonl \
        --out results-w1-short-files.json

    python3 -B score.py gate --freeze FREEZE.json --results results-w1-short-files.json \
        results-w2-message-entries.json --out gate.json

Environment: FAIR_BASELINES_FSST_SRC (the reference FSST sources), optionally
FAIR_BASELINES_BUILD_DIR (where native helpers are built; outside the repository).

`run` makes no choice of its own. The candidate's recipe and seed, every baseline's level,
dictionary kind and size, the index form, the verification order, the timing loop, the number
of lookups and rounds, the percentile, the quiet-window rule and the two gate numbers are all
read from FREEZE.json. Before anything is measured the run checks, against FREEZE.json, the
hash of every lane, harness, freeze-tool and FSST source file, the zstd and zlib library
versions, and the hash of the training file; after fitting it checks every fitted model
against the hash recorded at the freeze. Any difference stops the run with status `void`:
a void run is not a result.

Steps, per method, all through the harness's own `fb_measure.measure`:
  fit on the training records with the pinned setting; encode the test records once;
  serialise with one 4-byte offset per record; open a reader on the serialised bytes alone;
  decode every record on its own in a seeded random order and compare with the original.
Then one timing pass over all methods with the harness's `fb_time_lookups` loop
(`Native.time_lookups`), rounds interleaved across methods.

`--sizes-only` skips the timing pass. It exists for the repeat check (two runs must give the
same archives); a run made with it carries no gate verdict.

The results file holds settings, counts, hashes and timings. It holds no record content, no
source names and no paths.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import platform
import random
import statistics
import struct
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import freeze_common as F  # noqa: E402
from freeze_common import C, K, N  # noqa: E402
import fb_measure as M  # noqa: E402
from fb_candidate import CandidateAdapter  # noqa: E402

SCHEMA = 'short-record-decision/score/v1'
FREEZE_TOOL_FILES = tuple((HERE / n).relative_to(F.LITERALS).as_posix()
                          for n in ('bits_adapter.py', 'bits_native_shim.c', 'freeze_common.py', 'score.py'))
TIMING_SEED = 0x9E3779B97F4A7C15   # the constant fb_measure._native_timing passes to the loop


class Void(Exception):
    """The run cannot produce a result as pinned."""


def date_utc() -> str:
    return subprocess.run(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'], capture_output=True, text=True).stdout.strip()


def public_arg(arg: str) -> str:
    """Command-line argument as recorded in a results file: any path is reduced to its last part."""
    return '<dir>/' + arg.rstrip('/').rsplit('/', 1)[-1] if '/' in arg else arg


def load1() -> float | None:
    try:
        return round(os.getloadavg()[0], 2)
    except (OSError, AttributeError):
        return None


def cc_version() -> str | None:
    try:
        out = subprocess.run([os.environ.get('CC', 'cc'), '--version'], capture_output=True, text=True, timeout=10).stdout
        return out.splitlines()[0].strip() if out else None
    except Exception:
        return None


def compare_hashes(kind: str, pinned: dict, actual: dict, problems: list) -> dict:
    diff = sorted(k for k in set(pinned) | set(actual) if pinned.get(k) != actual.get(k))
    if diff:
        problems.append(f'{kind}: {len(diff)} file(s) differ from FREEZE.json: {diff}')
    return {'files': len(pinned), 'all_match': not diff, 'differing': diff}


# ---------------------------------------------------------------- measuring

def keep_last_encoding(codec) -> None:
    """Remember what `encode` returned, so the timing pass and the per-record sizes use the very
    archive the harness measured and verified."""
    inner = codec.encode

    def encode(records, groups=None):
        enc = inner(records, groups)
        codec._last_enc = enc
        return enc

    codec.encode = encode


def per_record_stored_bits(codec, archive4: bytes, n: int) -> list[int] | None:
    """Stored bits of each record, index excluded. None for block methods."""
    enc = getattr(codec, '_last_enc', None)
    if isinstance(enc, C.EncodedUnits):
        if enc.per_block != 1 or enc.parts is not None:
            return None
        return [8 * len(u) for u in enc.units]
    # candidate: BIT3 start bit offsets, one stream (layout A)
    n_entries, n_files, n_tables = struct.unpack_from('<HHB', archive4, 4)
    if n_tables != 1 or n_files != n:
        return None
    pos = 9
    for _ in range(n_entries):
        pos += 1 + archive4[pos]
    pos += n_entries + 1
    offs = list(struct.unpack_from(f'<{n}I', archive4, pos))
    end = 8 * (len(archive4) - pos - 4 * n)
    return [b - a for a, b in zip(offs, offs[1:] + [end])]


def source_bootstrap(sources: list[str], cand: dict, base: dict, spec: dict, ratio_max: Fraction) -> dict:
    """Interval for candidate total minus baseline total when the scored sources are resampled.

    Models and headers stay as fitted and stored; a resample changes which records are in the
    archive. Each resampled archive is charged its header, its model, 4 index bytes per record,
    the method's fixed per-record side bytes (the raw-block flag bitmap) and its stored bits
    rounded up to bytes."""
    labels = sorted(set(sources))
    by_src: dict[str, list[int]] = {s: [] for s in labels}
    for i, s in enumerate(sources):
        by_src[s].append(i)
    if len(labels) < 2:
        return {'status': 'not-run', 'reason': 'the scored records carry fewer than two source labels'}

    def per_source(bits):
        return [(len(by_src[s]), sum(bits[i] for i in by_src[s])) for s in labels]

    cs, bs = per_source(cand['bits']), per_source(base['bits'])

    def total(fixed: int, flag_bitmap: bool, picks, table) -> int:
        nrec = sum(table[j][0] for j in picks)
        bits = sum(table[j][1] for j in picks)
        return fixed + 4 * nrec + ((nrec + 7) // 8 if flag_bitmap else 0) + (bits + 7) // 8

    rng = random.Random(int(spec['seed']))
    k = len(labels)
    diffs, ratios = [], []
    for _ in range(int(spec['resamples'])):
        picks = [rng.randrange(k) for _ in range(k)]
        ct = total(cand['fixed'], cand['flag_bitmap'], picks, cs)
        bt = total(base['fixed'], base['flag_bitmap'], picks, bs)
        diffs.append(ct - bt)
        ratios.append(ct / bt)
    diffs.sort()
    ratios.sort()
    tail = (1 - Fraction(str(spec['level']))) / 2
    lo, hi = tail, 1 - tail

    def pct(vals, q: Fraction):   # nearest rank
        return vals[max(1, math.ceil(q * len(vals))) - 1]

    half = Fraction(1, 2)
    full = list(range(k))
    return {
        'status': 'ok', 'unit': 'source', 'sources': k, 'resamples': len(diffs), 'seed': int(spec['seed']), 'level': str(spec['level']),
        'check_identity_resample': {'candidate_total': total(cand['fixed'], cand['flag_bitmap'], full, cs),
                                    'baseline_total': total(base['fixed'], base['flag_bitmap'], full, bs)},
        'candidate_minus_baseline_bytes': {'low': pct(diffs, lo), 'median': pct(diffs, half), 'high': pct(diffs, hi)},
        'candidate_over_baseline_ratio': {'low': round(pct(ratios, lo), 5), 'median': round(pct(ratios, half), 5),
                                          'high': round(pct(ratios, hi), 5)},
        'share_of_resamples_with_ratio_at_most_gate': round(sum(1 for r in ratios if Fraction(r) <= ratio_max) / len(ratios), 4),
        'note': 'the baseline is the one that is strongest on the full scored set; models are not refitted per resample',
    }


def cold_first_lookup_us(open_reader, cap: int) -> float | None:
    """Open a reader on the archive and decode record 0, timed from Python (includes the foreign
    call overhead, the same for every method). Reported apart from the warm lookup time."""
    try:
        t0 = time.perf_counter_ns()
        rd = open_reader()
        rd.decode(0, cap)
        dt = time.perf_counter_ns() - t0
        M._close(rd)
        return round(dt / 1000.0, 1)
    except Exception:
        return None


def timing_pass(native, timed: list[dict], n: int, cap: int, spec: dict) -> dict:
    """Interleaved rounds of the harness's lookup loop over every method."""
    rounds, lookups, warmup = int(spec['rounds']), int(spec['lookups_per_round']), int(spec['warmup_lookups'])
    readers = []
    for t in timed:
        rd = t['open']()
        readers.append(rd)
        t['rounds'] = []
    start_load, started = load1(), date_utc()
    t0 = time.perf_counter()
    try:
        for r in range(rounds):
            order = list(range(len(timed)))
            order = order[r % len(order):] + order[:r % len(order)]   # rotate the starting method each round
            for j in order:
                rd = readers[j]
                timed[j]['rounds'].append(native.time_lookups(rd.decode_fn_addr, rd.handle, n, n_lookups=lookups, warmup=warmup,
                                                             seed=TIMING_SEED, out_cap=cap))
    finally:
        for rd in readers:
            M._close(rd)
    end_load = load1()
    quiet = spec['quiet_window']
    ok = (start_load is not None and end_load is not None
          and start_load <= float(quiet['max_load_average_1m_at_start']) and end_load <= float(quiet['max_load_average_1m_at_end']))
    out = {}
    med = statistics.median
    for t in timed:
        rs = t['rounds']
        best = min(rs, key=lambda x: x['loop_mean_ns'])
        out[t['name']] = {
            'kind': 'native-loop', 'lookups_per_round': lookups, 'rounds': rounds,
            'median_of_rounds': {
                'per_record_mean_p95_ns': round(med(x['per_record_mean_p95_ns'] for x in rs), 2),
                'per_record_mean_median_ns': round(med(x['per_record_mean_median_ns'] for x in rs), 2),
                'single_lookup_p95_ns': round(med(x['single_lookup_p95_ns'] for x in rs), 2),
                'single_lookup_median_ns': round(med(x['single_lookup_median_ns'] for x in rs), 2),
                'loop_mean_ns': round(med(x['loop_mean_ns'] for x in rs), 2),
            },
            'least_disturbed_round': {k: best[k] for k in ('loop_mean_ns', 'per_record_mean_median_ns', 'per_record_mean_p95_ns',
                                                           'single_lookup_median_ns', 'single_lookup_p95_ns')},
            'all_rounds': [{k: x[k] for k in ('loop_mean_ns', 'per_record_mean_median_ns', 'per_record_mean_p95_ns',
                                              'single_lookup_median_ns', 'single_lookup_p95_ns', 'single_lookup_p99_ns',
                                              'records_visited', 'interrupted_samples_left_out_of_per_record_means',
                                              'decoded_mib_per_sec')} for x in rs],
        }
    return {
        'started_utc': started, 'seconds': round(time.perf_counter() - t0, 1),
        'load_average_1m_at_start': start_load, 'load_average_1m_at_end': end_load,
        'quiet_window_rule': quiet, 'quiet_window_ok': bool(ok),
        'timer': native.timer_probe(), 'methods': out,
    }


# ---------------------------------------------------------------- run

def run(args) -> int:
    F.scrub_env_for_scoring()
    started = date_utc()
    t_start = time.perf_counter()
    freeze_path = Path(args.freeze)
    freeze_raw = freeze_path.read_bytes()
    fz = json.loads(freeze_raw)
    wl = fz['workloads'][args.workload]
    rule = fz['decision_rule']
    acc = fz['byte_accounting']
    doc: dict = {
        'schema': SCHEMA, 'workload': args.workload, 'workload_role': wl['role'],
        'command': ['python3', '-B', 'score.py', *[public_arg(a) for a in sys.argv[1:]]],
        'started_utc': started,
        'freeze': {'sha256': hashlib.sha256(freeze_raw).hexdigest(), 'frozen_utc': fz['times_utc']['frozen']},
        'sizes_only': bool(args.sizes_only),
    }
    problems: list[str] = []

    def finish(status: str, code: int) -> int:
        doc['status'] = status
        doc['void_reasons'] = problems
        doc['finished_utc'] = date_utc()
        doc['elapsed_seconds'] = round(time.perf_counter() - t_start, 1)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(doc, indent=1) + '\n', encoding='utf-8')
        print(f'\nstatus: {status}' + (''.join(f'\n  void: {p}' for p in problems)))
        print(f'wrote {out.name}')
        return code

    # ---- 1. everything that decides the result is what was frozen
    import bits_adapter as A
    pinned_files = fz['files']
    checks = {
        'lane': compare_hashes('lane files', pinned_files['lane'], A.lane_file_hashes(), problems),
        'harness': compare_hashes('harness files', pinned_files['harness'], F.file_hashes(F.HARNESS_FILES), problems),
        'freeze_tools': compare_hashes('freeze tools', pinned_files['freeze_tools'], F.file_hashes(FREEZE_TOOL_FILES), problems),
    }
    fsst_src = Path(args.fsst_src) if args.fsst_src else N.default_fsst_src()
    if fsst_src is None or not all((fsst_src / f).is_file() for f in F.FSST_FILES):
        problems.append('reference FSST sources not found; set FAIR_BASELINES_FSST_SRC')
    else:
        checks['fsst_reference'] = compare_hashes('reference FSST sources', pinned_files['fsst_reference']['files'],
                                                  F.file_hashes(F.FSST_FILES, fsst_src), problems)
    # recorded, not enforced: the custodian may fix the protocol's status line when the freeze is committed
    proto, mani = fz['protocol'], fz['corpus_manifest']
    checks['protocol_same_as_read_at_freeze'] = F.sha256_file(F.LITERALS / proto['file']) == proto['sha256']
    checks['corpus_manifest_same_as_read_at_freeze'] = F.sha256_file(F.LITERALS / mani['file']) == mani['sha256']
    doc['integrity'] = checks

    train_sha, test_sha = F.sha256_file(args.train), F.sha256_file(args.test)
    data = fz['data'][args.workload]
    if train_sha != data['train']['sha256']:
        problems.append('the training file is not the one named in FREEZE.json')
    role = ('test' if test_sha == data['test_sha256_from_manifest'] else
            'validation' if test_sha == data['validation']['sha256'] else 'unknown')
    doc['scored_records_role'] = role
    if problems:
        return finish('void', 2)

    native = F.load_native(fsst_src, args.build_dir)
    env = fz['environment']
    if native.zstd_version != env['zstd_library']:
        problems.append(f'zstd library {native.zstd_version} differs from the frozen {env["zstd_library"]}')
    if native.zlib_version != env['zlib_library']:
        problems.append(f'zlib library {native.zlib_version} differs from the frozen {env["zlib_library"]}')
    if not native.has_fsst:
        problems.append('the reference FSST was not built into the native helper')
    doc['environment'] = {
        'zstd_library': native.zstd_version, 'zlib_library': native.zlib_version, 'reference_fsst_built': native.has_fsst,
        'native_helper': native.facts, 'python': platform.python_version(), 'system': platform.system(),
        'machine': platform.machine(), 'cpu': M._cpu_brand(), 'cc': cc_version(), 'logical_cpus': os.cpu_count(),
        'python_differs_from_freeze': platform.python_version() != env['python'],
    }
    if problems:
        return finish('void', 2)

    train_records, _ = F.load_custody_jsonl(args.train)
    test_records, test_sources = F.load_custody_jsonl(args.test)
    train, test = F.record_set(train_records), F.record_set(test_records)
    doc['inputs'] = {'train': {**train.describe(), 'file_sha256': train_sha},
                     'scored': {**test.describe(), 'file_sha256': test_sha, 'sources': len(set(test_sources))}}
    print(f'{args.workload}: train {len(train)} records / {train.total_bytes} bytes; scored ({role}) {len(test)} records / {test.total_bytes} bytes')

    hs = fz['harness_settings']
    opts = M.Options(folds=int(hs['folds']), seed=int(hs['seed']), grid=hs['grid'], lookups=int(rule['lookup_timing']['lookups_per_round']),
                     rounds=int(rule['lookup_timing']['rounds']), warmup=int(rule['lookup_timing']['warmup_lookups']),
                     block_sizes=tuple(hs['block_sizes']), per_group=False, methods=None, timing=False)
    ctx = K.TuneContext(native, train.records, folds=opts.folds, seed=opts.seed, grid=opts.grid, groups=None)
    doc['options'] = {'verification_order_seed': opts.seed + 17, 'index_bytes_per_offset': C.LANE_INDEX_WIDTH,
                      'timing': rule['lookup_timing']}
    if int(acc['index_bytes_per_record']) != C.LANE_INDEX_WIDTH:
        problems.append('FREEZE.json pins an index width the harness does not serialise as its all-in form')
        return finish('void', 2)

    # ---- 2. fit, encode, account, verify: the harness's measure(), one method at a time
    plan = []   # (name, role, codec instance, pinned model hash or None)
    for name in wl['baselines']['per_record_order']:
        b = wl['baselines']['methods'][name]
        plan.append((name, 'per-record baseline', F.pinned_baseline_factory(native, name, b.get('setting'))(), b.get('model_sha256')))
    for name in wl['baselines']['blocks_order']:
        b = wl['baselines']['methods'][name]
        plan.append((name, 'small-block baseline', F.pinned_baseline_factory(native, name, b.get('setting'))(), b.get('model_sha256')))
    cand_cfg = dict(wl['candidate']['config'])
    cand_obj = A.Bit3Candidate(cand_cfg)
    cand_name = cand_obj.name
    plan.append((cand_name, 'candidate', CandidateAdapter(cand_obj), wl['candidate'].get('dictionary_sha256')))

    methods, archives, codecs = [], {}, {}
    cap = max(len(r) for r in test.records) + 64
    for name, mrole, codec, pinned_model in plan:
        t0 = time.perf_counter()
        keep_last_encoding(codec)
        m = M.measure(native, name, lambda codec=codec: codec, train, test, ctx, opts)
        m['role'] = mrole
        if m['status'] == 'ok':
            arc4, acct4 = codec._last_enc.pack(C.LANE_INDEX_WIDTH)
            if len(arc4) != m['bytes']['all_in']['total']:
                problems.append(f'{name}: the archive kept for timing is not the one that was measured')
            m['archive_sha256'] = hashlib.sha256(arc4).hexdigest()
            archives[name], codecs[name] = arc4, codec
            fitted = ((m.get('tuning') or {}).get('chosen') or {}).get('model_sha256') if mrole != 'candidate' else \
                (m.get('tuning') or {}).get('dictionary_sha256')
            m['fitted_model_sha256'] = fitted
            if pinned_model is not None:
                m['fitted_model_matches_freeze'] = (fitted == pinned_model)
                if fitted != pinned_model:
                    problems.append(f'{name}: the fitted model differs from the one recorded at the freeze')
            if mrole == 'candidate':
                m['candidate_encode'] = cand_obj.last_encode_report
                spec = A.build_native_decoder()
                m['memory']['reader_heap_peak_bytes'] = A.native_reader_heap_bytes(spec, arc4) if spec else None
                m['memory']['note'] = ('the lane\'s C reader state (fixed-size tables for 4,100 symbols and two code tables) '
                                       'plus a zero-padded private copy of the archive; stack is not counted')
                if 'native_decoder' not in m['verification']:
                    problems.append('the candidate\'s native decoder could not be built; its lookups cannot be timed in the shared loop')
        methods.append(m)
        total = (m.get('bytes') or {}).get('all_in', {}).get('total')
        print(f'  {name:32s} {m["status"]:20s} {"" if total is None else total:>9} bytes  ({time.perf_counter() - t0:.1f}s)', flush=True)
    doc['methods'] = methods
    by = {m['name']: m for m in methods}
    if by[cand_name]['status'] in ('error', 'not-applicable'):
        if cand_obj.entries is not None and cand_obj.train_report:
            # The dictionary was fitted; the failure came when storing the scored records. That is a
            # property of the candidate on these records, not of the run.
            fitted = cand_obj.train_report.get('dictionary_sha256')
            by[cand_name]['fitted_model_sha256'] = fitted
            by[cand_name]['fitted_model_matches_freeze'] = (fitted == wl['candidate'].get('dictionary_sha256'))
            if not by[cand_name]['fitted_model_matches_freeze']:
                problems.append(f'{cand_name}: the fitted model differs from the one recorded at the freeze')
            by[cand_name]['status'] = 'cannot-encode'
        else:
            problems.append(f'candidate could not be fitted as pinned: {by[cand_name].get("reason")}')
    for name, mrole, _, _ in plan:
        if mrole != 'candidate' and by[name]['status'] in ('error', 'not-applicable'):
            problems.append(f'{name} could not be run as pinned: {by[name].get("reason")}')
    if problems:
        return finish('void', 2)

    # ---- 3. the strongest per-record baseline, by total bytes
    def total_of(name):
        return by[name]['bytes']['all_in']['total']

    eligible = [n for n in wl['baselines']['per_record_order'] if by[n]['status'] == 'ok']
    disqualified = [m['name'] for m in methods if m['status'] == 'failed-verification']
    strongest = min(eligible, key=lambda n: (total_of(n), wl['baselines']['per_record_order'].index(n))) if eligible else None
    cand_ok = by[cand_name]['status'] == 'ok'
    ratio_max = Fraction(str(rule['bytes']['candidate_total_at_most_fraction_of_strongest_per_record_baseline']))
    p95_max = Fraction(str(rule['lookup']['candidate_p95_at_most_fraction_of_that_baseline']))

    # ---- 4. spread of the byte difference over sources
    if cand_ok and strongest:
        def parts(name):
            a = by[name]['bytes']['all_in']
            bits = per_record_stored_bits(codecs[name], archives[name], len(test))
            aux = len(getattr(codecs[name]._last_enc, 'aux', b'') or b'') if isinstance(codecs[name]._last_enc, C.EncodedUnits) else 0
            fixed = a['total'] - 4 * len(test) - aux - (sum(bits) + 7) // 8 if bits is not None else None
            return {'bits': bits, 'fixed': fixed, 'flag_bitmap': aux > 0}
        pc, pb = parts(cand_name), parts(strongest)
        if pc['bits'] is None or pb['bits'] is None:
            doc['spread'] = {'status': 'not-run', 'reason': 'per-record stored sizes are not available for one of the two methods'}
        else:
            doc['spread'] = source_bootstrap(test_sources, pc, pb, rule['spread'], ratio_max)
            ident = doc['spread'].get('check_identity_resample')
            if ident and (ident['candidate_total'] != total_of(cand_name) or ident['baseline_total'] != total_of(strongest)):
                doc['spread']['status'] = 'inconsistent'
                doc['spread']['reason'] = 'the per-record sizes do not add up to the measured totals'

    # ---- 5. timing: one loop, every method, interleaved rounds
    timing = None
    if not args.sizes_only:
        timed = []
        for name, mrole, codec, _ in plan:
            if by[name]['status'] != 'ok':
                continue
            arc = archives[name]
            if mrole == 'candidate':
                opener = (lambda codec=codec, arc=arc: codec.native_reader(arc))
            else:
                opener = (lambda codec=codec, arc=arc: codec.open_reader(native, arc))
            by[name]['cold_open_plus_first_lookup_us'] = cold_first_lookup_us(opener, cap)
            timed.append({'name': name, 'open': opener})
        timing = timing_pass(native, timed, len(test), cap, rule['lookup_timing'])
        for name, t in timing['methods'].items():
            by[name]['lookup_timing'] = t
        doc['timing_pass'] = {k: v for k, v in timing.items() if k != 'methods'}

    # ---- 6. table and gate
    stat = rule['lookup']['statistic']
    table = []
    for m in methods:
        row = {'method': m['name'], 'role': m['role'], 'status': m['status']}
        if m['status'] == 'ok':
            a = m['bytes']['all_in']
            row.update(total_bytes=a['total'], header=a['header'], model=a['model'], index=a['index'], framing=a['framing'],
                       payload=a['payload'], payload_only_bytes=a['payload'],
                       total_with_smallest_whole_byte_index=(m['bytes']['all_in_compact_index'] or {}).get('total'),
                       exact_reconstruction=all(v.get('ok') for v in m['verification'].values() if isinstance(v, dict)),
                       records_verified={k: v.get('records_checked') for k, v in m['verification'].items() if isinstance(v, dict)},
                       mean_raw_bytes_decoded_per_lookup=(m.get('per_lookup') or {}).get('mean_raw_bytes_decoded'),
                       build_seconds=round(m['build']['tune_and_fit_sec'] + m['build']['encode_test_sec'], 2),
                       reader_heap_peak_bytes=(m.get('memory') or {}).get('reader_heap_peak_bytes'),
                       cold_open_plus_first_lookup_us=m.get('cold_open_plus_first_lookup_us'))
            t = (m.get('lookup_timing') or {}).get('median_of_rounds')
            if t:
                row.update(lookup_median_ns=t['per_record_mean_median_ns'], lookup_p95_ns=t[stat],
                           single_lookup_median_ns=t['single_lookup_median_ns'], single_lookup_p95_ns=t['single_lookup_p95_ns'],
                           loop_mean_ns=t['loop_mean_ns'])
        else:
            row['exact_reconstruction'] = False if m['status'] == 'failed-verification' else None
            row['reason'] = m.get('reason') or m.get('verification')
        table.append(row)
    doc['table'] = table

    gate: dict = {
        'rule': {'bytes': rule['bytes'], 'lookup': rule['lookup'], 'decision_workloads': rule['decision_workloads'],
                 'passed_only_if_both_conditions_hold_on_both_decision_workloads': True},
        'scored_records_role': role,
        'strongest_per_record_baseline': strongest,
        'per_record_baselines_considered': eligible,
        'methods_disqualified_by_a_mismatch': disqualified,
    }
    if not cand_ok:
        gate.update(bytes_condition_met=False, lookup_condition_met=False, workload_conditions_met=False,
                    reason='the candidate did not reconstruct every record exactly' if by[cand_name]['status'] == 'failed-verification'
                    else 'the candidate could not store the scored records: ' + str(by[cand_name].get('reason')))
    elif strongest is None:
        problems.append('no per-record baseline ran and verified')
        return finish('void', 2)
    else:
        ct, bt = total_of(cand_name), total_of(strongest)
        bt_compact = (by[strongest]['bytes']['all_in_compact_index'] or {'total': bt})['total']
        gate.update(candidate_total_bytes=ct, baseline_total_bytes=bt, bytes_ratio=round(ct / bt, 5),
                    bytes_ratio_allowed_at_most=str(rule['bytes']['candidate_total_at_most_fraction_of_strongest_per_record_baseline']),
                    bytes_condition_met=bool(Fraction(ct, bt) <= ratio_max),
                    candidate_minus_baseline_bytes=ct - bt,
                    candidate_payload_only_bytes=by[cand_name]['bytes']['all_in']['payload'],
                    baseline_payload_only_bytes=by[strongest]['bytes']['all_in']['payload'],
                    information_only_not_part_of_the_gate={
                        'baseline_total_with_smallest_whole_byte_index': bt_compact,
                        'bytes_ratio_if_only_the_baseline_used_that_index': round(ct / bt_compact, 5),
                        'note': 'the candidate\'s container has no index form other than 4 bytes per record',
                    })
        if timing is None:
            gate.update(lookup_condition_met=None, workload_conditions_met=None,
                        reason='sizes-only run: no timing, no verdict')
        else:
            cp = by[cand_name]['lookup_timing']['median_of_rounds'][stat]
            bp = by[strongest]['lookup_timing']['median_of_rounds'][stat]
            lookup_ok = Fraction(str(cp)) <= p95_max * Fraction(str(bp))
            gate.update(candidate_lookup_p95_ns=cp, baseline_lookup_p95_ns=bp, lookup_p95_ratio=round(cp / bp, 4) if bp else None,
                        lookup_p95_ratio_allowed_at_most=str(rule['lookup']['candidate_p95_at_most_fraction_of_that_baseline']), lookup_statistic=stat,
                        candidate_lookup_median_ns=by[cand_name]['lookup_timing']['median_of_rounds']['per_record_mean_median_ns'],
                        baseline_lookup_median_ns=by[strongest]['lookup_timing']['median_of_rounds']['per_record_mean_median_ns'],
                        timing_valid=timing['quiet_window_ok'])
            if timing['quiet_window_ok']:
                gate.update(lookup_condition_met=bool(lookup_ok), workload_conditions_met=bool(gate['bytes_condition_met'] and lookup_ok))
            elif not gate['bytes_condition_met']:
                # Both conditions are needed. With the bytes condition not met the workload cannot meet the
                # gate, whatever a valid timing would show.
                gate.update(lookup_condition_met=None, workload_conditions_met=False, lookup_condition_as_measured=bool(lookup_ok),
                            reason='the bytes condition is not met, which settles this workload; the timing pass did not run in a '
                                   'quiet window as pinned, so its numbers are void and are shown for information only')
            else:
                gate.update(lookup_condition_met=None, workload_conditions_met=None, lookup_condition_as_measured=bool(lookup_ok),
                            reason='the timing pass did not run in a quiet window as pinned; the timing is void and the scoring '
                                   'command is run again unchanged')
    gate['label'] = ('scored on the sealed test records' if role == 'test' else
                     f'DRY RUN on {role} records: decides nothing')
    doc['gate'] = gate

    det = {m['name']: {'status': m['status'], 'all_in': (m.get('bytes') or {}).get('all_in'), 'archive_sha256': m.get('archive_sha256'),
                       'fitted_model_sha256': m.get('fitted_model_sha256')} for m in methods}
    doc['deterministic_part'] = {'sha256': hashlib.sha256(json.dumps(det, sort_keys=True).encode()).hexdigest(), 'content': det}

    print()
    print(f'{"method":32s} {"role":22s} {"total":>9s} {"model":>7s} {"index":>7s} {"framing":>7s} {"payload":>9s} {"exact":>6s} {"median ns":>10s} {"p95 ns":>9s}')
    def ns(v, width):
        return f'{v:{width}.1f}' if isinstance(v, (int, float)) else f'{"-":>{width}s}'

    for r in table:
        if r['status'] != 'ok':
            print(f'{r["method"]:32s} {r["role"]:22s} {r["status"]}')
            continue
        print(f'{r["method"]:32s} {r["role"]:22s} {r["total_bytes"]:9d} {r["model"]:7d} {r["index"]:7d} {r["framing"]:7d} '
              f'{r["payload"]:9d} {str(r["exact_reconstruction"]):>6s} {ns(r.get("lookup_median_ns"), 10)} {ns(r.get("lookup_p95_ns"), 9)}')
    print()
    print(json.dumps({k: v for k, v in gate.items() if k != 'rule'}, indent=1))
    if args.sizes_only:
        return finish('ok-sizes-only', 0)
    if gate.get('workload_conditions_met') is None:
        return finish('timing-void', 3)
    return finish('ok', 0)


# ---------------------------------------------------------------- gate over the decision workloads

def gate(args) -> int:
    fz_raw = Path(args.freeze).read_bytes()
    fz = json.loads(fz_raw)
    rule = fz['decision_rule']
    need = list(rule['decision_workloads'])
    docs = [json.loads(Path(p).read_text(encoding='utf-8')) for p in args.results]
    fsha = hashlib.sha256(fz_raw).hexdigest()
    by = {d['workload']: d for d in docs}
    out: dict = {'schema': 'short-record-decision/gate/v1', 'written_utc': date_utc(), 'freeze_sha256': fsha,
                 'decision_workloads': need, 'workloads': {}, 'problems': []}
    roles = set()
    for w, d in by.items():
        g = d.get('gate') or {}
        out['workloads'][w] = {
            'workload_role': d.get('workload_role'), 'status': d.get('status'), 'scored_records_role': d.get('scored_records_role'),
            'strongest_per_record_baseline': g.get('strongest_per_record_baseline'),
            'candidate_total_bytes': g.get('candidate_total_bytes'), 'baseline_total_bytes': g.get('baseline_total_bytes'),
            'bytes_ratio': g.get('bytes_ratio'), 'bytes_condition_met': g.get('bytes_condition_met'),
            'candidate_lookup_p95_ns': g.get('candidate_lookup_p95_ns'), 'baseline_lookup_p95_ns': g.get('baseline_lookup_p95_ns'),
            'lookup_p95_ratio': g.get('lookup_p95_ratio'), 'lookup_condition_met': g.get('lookup_condition_met'),
            'workload_conditions_met': g.get('workload_conditions_met'),
            'results_sha256': hashlib.sha256(Path(next(p for p, dd in zip(args.results, docs) if dd is d)).read_bytes()).hexdigest(),
        }
        if (d.get('freeze') or {}).get('sha256') != fsha:
            out['problems'].append(f'{w}: scored against a different FREEZE.json')
        if w in need:
            roles.add(d.get('scored_records_role'))
    missing = [w for w in need if w not in by]
    if missing:
        out['problems'].append(f'no results for decision workload(s) {missing}')
    undecided = [w for w in need if w in by and (by[w].get('status') != 'ok' or by[w]['gate'].get('workload_conditions_met') is None)]
    if undecided:
        out['problems'].append(f'no valid verdict for {undecided} (void run, void timing, or sizes-only)')
    if out['problems']:
        out['verdict'] = 'no verdict'
    else:
        out['verdict'] = 'passed' if all(by[w]['gate']['workload_conditions_met'] for w in need) else 'not passed'
    out['label'] = ('scored on the sealed test records' if roles == {'test'} else
                    'DRY RUN, not on the sealed test records: decides nothing')
    if args.embed:
        out['results'] = by
    Path(args.out).write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in out.items() if k != 'results'}, indent=1))
    return 0 if not out['problems'] else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run', help='score one workload')
    r.add_argument('--freeze', required=True)
    r.add_argument('--workload', required=True, choices=F.WORKLOADS)
    r.add_argument('--train', required=True, help='the workload\'s training records (custody JSONL)')
    r.add_argument('--test', required=True, help='the records to score (custody JSONL)')
    r.add_argument('--out', required=True)
    r.add_argument('--fsst-src', help='reference FSST sources (or FAIR_BASELINES_FSST_SRC)')
    r.add_argument('--build-dir', help='where native helpers are built (or FAIR_BASELINES_BUILD_DIR)')
    r.add_argument('--sizes-only', action='store_true', help='no timing pass and no verdict (repeat check only)')
    r.set_defaults(fn=run)
    g = sub.add_parser('gate', help='combine the decision workloads\' results into the gate verdict')
    g.add_argument('--freeze', required=True)
    g.add_argument('--results', nargs='+', required=True)
    g.add_argument('--out', required=True)
    g.add_argument('--embed', action='store_true', help='copy the per-workload results into the output')
    g.set_defaults(fn=gate)
    args = ap.parse_args()
    if getattr(args, 'build_dir', None):
        os.environ['FAIR_BASELINES_BUILD_DIR'] = str(args.build_dir)
    return args.fn(args)


if __name__ == '__main__':
    raise SystemExit(main())
