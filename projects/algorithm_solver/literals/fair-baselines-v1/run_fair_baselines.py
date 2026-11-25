#!/usr/bin/env python3
"""Run every baseline (and any candidate codec) on a train input and a test input.

    python3 run_fair_baselines.py --train TRAIN --test TEST --out results/my_run.json \
        [--fsst-src DIR] [--candidate path/to/adapter.py:ClassName] [--grid quick]

TRAIN and TEST are each a directory (one record per file; an optional first-level subdirectory
names the record's group) or a JSONL file (see fb_core.load_records). Settings are chosen on
TRAIN only. TEST is encoded once with the chosen settings, verified and timed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import fb_core as C  # noqa: E402
import fb_measure as M  # noqa: E402
import fb_native as N  # noqa: E402
from fb_candidate import load_candidate  # noqa: E402


def add_common_args(ap: argparse.ArgumentParser) -> None:
    ap.add_argument('--fsst-src', help='checkout of github.com/cwida/fsst (or set FAIR_BASELINES_FSST_SRC)')
    ap.add_argument('--build-dir', help='where to build the native helper (default: system temp directory)')
    ap.add_argument('--grid', choices=['full', 'quick'], default='full', help='tuning grid')
    ap.add_argument('--folds', type=int, default=4, help='cross-validation folds inside the training input')
    ap.add_argument('--seed', type=int, default=1, help='seed for the fold split and the verification order')
    ap.add_argument('--lookups', type=int, default=200_000, help='timed lookups per round')
    ap.add_argument('--rounds', type=int, default=5, help='timing rounds per method; the least disturbed round is reported')
    ap.add_argument('--block-sizes', default='2,4,8,16', help='records per block for the small-block baselines')
    ap.add_argument('--methods', help='comma-separated subset of method names')
    ap.add_argument('--no-per-group', action='store_true', help='skip the one-model-per-group variants')
    ap.add_argument('--no-timing', action='store_true', help='sizes and verification only')
    ap.add_argument('--candidate', action='append', default=[], help='path/to/file.py:ClassName (repeatable)')


def options_from_args(args) -> M.Options:
    return M.Options(
        folds=args.folds, seed=args.seed, grid=args.grid, lookups=args.lookups, rounds=args.rounds,
        block_sizes=tuple(int(x) for x in args.block_sizes.split(',') if x),
        per_group=not args.no_per_group, methods=tuple(args.methods.split(',')) if args.methods else None,
        timing=not args.no_timing)


def load_native_from_args(args) -> tuple[N.Native, Path | None]:
    fsst_src = Path(args.fsst_src) if args.fsst_src else N.default_fsst_src()
    native = N.load_native(fsst_src, Path(args.build_dir) if args.build_dir else None)
    if not native.has_fsst:
        print('note: reference FSST sources not given; the reference FSST baseline will be reported as '
              'not applicable (the lane\'s own implementation still runs, labelled as such)', file=sys.stderr)
    return native, fsst_src


def summary_rows(doc: dict) -> list[dict]:
    rows = []
    for m in doc['methods']:
        row = {'method': m['name'], 'table': m.get('table'), 'status': m['status']}
        if m['status'] == 'ok':
            b, t = m['bytes'], m.get('lookup_timing') or {}
            row.update(
                like_for_like_lane_form=b['like_for_like_lane_form'],
                all_in=b['all_in']['total'],
                all_in_compact_index=(b['all_in_compact_index'] or {}).get('total'),
                model=b['all_in']['model'], index=b['all_in']['index'], framing=b['all_in']['framing'],
                payload=b['all_in']['payload'],
                loop_mean_ns=t.get('loop_mean_ns'),
                per_record_median_ns=t.get('per_record_mean_median_ns', t.get('single_lookup_median_ns')),
                per_record_p95_ns=t.get('per_record_mean_p95_ns', t.get('single_lookup_p95_ns')),
                timing_kind=t.get('kind'),
                reader_heap_peak_bytes=(m.get('memory') or {}).get('reader_heap_peak_bytes'),
                build_sec=round(m['build']['tune_and_fit_sec'] + m['build']['encode_test_sec'], 3),
                mean_raw_bytes_decoded_per_lookup=(m.get('per_lookup') or {}).get('mean_raw_bytes_decoded'),
            )
        else:
            row['reason'] = m.get('reason') or (m.get('verification') or {})
        rows.append(row)
    return rows


def print_summary(doc: dict) -> None:
    print(f'{"method":40s} {"status":12s} {"lane-form":>9s} {"all-in":>8s} {"compact":>8s} {"model":>6s} '
          f'{"framing":>7s} {"payload":>8s} {"ns/lookup":>9s} {"p95 ns":>8s}')
    for r in summary_rows(doc):
        if r['status'] != 'ok':
            print(f'{r["method"]:40s} {r["status"]}: {r.get("reason")}')
            continue
        dash = lambda v, w: f'{v:{w}d}' if v is not None else ' ' * (w - 1) + '-'   # noqa: E731
        print(f'{r["method"]:40s} {r["status"]:12s} {dash(r["like_for_like_lane_form"], 9)} {r["all_in"]:8d} '
              f'{dash(r["all_in_compact_index"], 8)} {r["model"]:6d} {r["framing"]:7d} {r["payload"]:8d} '
              f'{r["loop_mean_ns"] or float("nan"):9.1f} {r["per_record_p95_ns"] or float("nan"):8.1f}'
              f'{"" if r["timing_kind"] == "native-loop" else "  (" + str(r["timing_kind"]) + ")"}')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--train', required=True, help='training records (directory or JSONL)')
    ap.add_argument('--test', required=True, help='test records (directory or JSONL)')
    ap.add_argument('--out', required=True, help='results JSON to write')
    add_common_args(ap)
    args = ap.parse_args()
    native, fsst_src = load_native_from_args(args)
    train, test = C.load_records(args.train), C.load_records(args.test)
    candidates = [load_candidate(spec) for spec in args.candidate]
    print(f'train: {len(train)} records, {train.total_bytes} bytes; test: {len(test)} records, {test.total_bytes} bytes')
    doc = M.run(native, train, test, options_from_args(args), candidates=candidates, fsst_src=fsst_src,
                command=['python3', Path(sys.argv[0]).name, *sys.argv[1:]], progress=print)
    doc['summary'] = summary_rows(doc)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8')
    print()
    print_summary(doc)
    print(f'\nwrote {out}')
    return 0 if all(m['status'] != 'failed-verification' for m in doc['methods']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
