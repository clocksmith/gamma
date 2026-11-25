#!/usr/bin/env python3
# UNFINISHED. Part of a short-record-decision freeze that was paused before FREEZE.json was written.
# Nothing here is pinned. See ../FREEZE-PROGRESS.md for what was run, what was never run, and the next steps.
"""Measure one candidate configuration: fit on training records, encode the validation records.

    python3 -B explore_candidate.py --workload w1-short-files --train TRAIN.jsonl \
        --validation VALIDATION.jsonl --config '{"selection": "transfer_vmm", "k_max": 1024}' \
        --log tried.jsonl

Used by the freeze owner to fill the table of configurations tried. One JSON line is appended
to the log per run: the configuration, what the fit produced, the all-in bytes of the
validation archive by part, and whether every validation record, decoded alone in a seeded
random order, equals the original. The log holds settings, counts and hashes only.

BITS_ADAPTER_CACHE_DIR may be set to reuse a dictionary fitted earlier for the same
configuration, records and lane files.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import random
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bits_adapter as A  # noqa: E402
import freeze_common as F  # noqa: E402


def date_utc() -> str:
    return subprocess.run(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'], capture_output=True, text=True).stdout.strip()


def verify_python(reader, records, seed: int) -> dict:
    order = list(range(len(records)))
    random.Random(seed).shuffle(order)
    for k, i in enumerate(order):
        if reader.decode(i) != records[i]:
            return {'ok': False, 'records_checked': k, 'first_bad_record': i}
    return {'ok': True, 'records_checked': len(records)}


def verify_native(spec: dict, archive: bytes, records, seed: int) -> dict:
    lib = ctypes.CDLL(spec['library'])
    lib.bits_bit3_open.restype = ctypes.c_void_p
    lib.bits_bit3_open.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
    lib.bits_bit3_decode.restype = ctypes.c_size_t
    lib.bits_bit3_decode.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_size_t]
    lib.bits_bit3_close.argtypes = [ctypes.c_void_p]
    h = lib.bits_bit3_open(archive, len(archive))
    if not h:
        return {'ok': False, 'problem': 'native open returned NULL'}
    cap = max(len(r) for r in records) + 64
    buf = ctypes.create_string_buffer(cap + 64)
    order = list(range(len(records)))
    random.Random(seed).shuffle(order)
    try:
        for k, i in enumerate(order):
            n = lib.bits_bit3_decode(h, i, buf, cap)
            if n == ctypes.c_size_t(-1).value or buf.raw[:n] != records[i]:
                return {'ok': False, 'records_checked': k, 'first_bad_record': i}
    finally:
        lib.bits_bit3_close(h)
    return {'ok': True, 'records_checked': len(records)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--workload', required=True)
    ap.add_argument('--train', required=True)
    ap.add_argument('--validation', required=True)
    ap.add_argument('--config', required=True, help='JSON object, see bits_adapter.DEFAULT_CONFIG')
    ap.add_argument('--log', required=True)
    ap.add_argument('--seed', type=int, default=18, help='seed of the verification order')
    ap.add_argument('--no-native', action='store_true')
    args = ap.parse_args()

    started = date_utc()
    t0 = time.perf_counter()
    train, _ = F.load_custody_jsonl(args.train)
    val, _ = F.load_custody_jsonl(args.validation)
    cand = A.Bit3Candidate(json.loads(args.config))
    row: dict = {'workload': args.workload, 'config': cand.cfg, 'started_utc': started,
                 'train_sha256': F.sha256_file(args.train), 'validation_sha256': F.sha256_file(args.validation)}
    try:
        rep = cand.train(train, None)
        t1 = time.perf_counter()
        res = cand.encode(val, None)
        t2 = time.perf_counter()
        acct = dict(res['accounting'])
        acct['total'] = sum(acct.values())
        assert acct['total'] == len(res['archive'])
        row.update(status='ok', fit=rep, validation_all_in=acct, encode=cand.last_encode_report,
                   encode_seconds=round(t2 - t1, 1))
        row['verification'] = {'python_reader': verify_python(cand.open(res['archive']), val, args.seed)}
        if not args.no_native:
            spec = A.build_native_decoder()
            row['verification']['native_reader'] = (verify_native(spec, res['archive'], val, args.seed) if spec
                                                    else {'ok': None, 'problem': 'native decoder not built'})
    except Exception as exc:   # a configuration the lane's code cannot run is a result, not a crash
        row.update(status='error', reason=f'{type(exc).__name__}: {exc}')
    row['finished_utc'] = date_utc()
    row['seconds'] = round(time.perf_counter() - t0, 1)
    with open(args.log, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(row, sort_keys=True) + '\n')
    brief = {k: row.get(k) for k in ('workload', 'status', 'reason', 'seconds')}
    if row['status'] == 'ok':
        brief.update(total=row['validation_all_in']['total'], model=row['validation_all_in']['model'],
                     payload=row['validation_all_in']['payload'], entries=row['fit']['dictionary_entries'],
                     unseen=row['encode']['unseen_single_bytes_added'], verified=row['verification'])
    print(json.dumps({'config': cand.cfg, **brief}), flush=True)
    return 0 if row['status'] == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
