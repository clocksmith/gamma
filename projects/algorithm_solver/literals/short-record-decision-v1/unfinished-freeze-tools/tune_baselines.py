#!/usr/bin/env python3
# UNFINISHED. Part of a short-record-decision freeze that was paused before FREEZE.json was written.
# Nothing here is pinned. See ../FREEZE-PROGRESS.md for what was run, what was never run, and the next steps.
"""Tune the baselines of one workload on its training and validation records.

    python3 -B tune_baselines.py --workload w1-short-files --train TRAIN.jsonl \
        --validation VALIDATION.jsonl --out tuning.json [--harness-cv]

The grid, the dictionary trainers and the encoders are the harness's own
(`../fair-baselines-v1/fb_codecs.py`, grid `full`). What differs from the harness's default run
is the objective, and only that:

  harness default   4-fold cross-validation inside the training input, folds drawn by record
  here              fit on the whole training input, measure on the validation records

The workloads are split by source. Record-level folds put records of one source on both sides
of a fold, so they reward dictionaries that memorise a source; the validation split holds
sources the model has not seen, and has as many records as the test split, which is the
situation the pinned setting will be scored in. The candidate's configuration is chosen with
the same objective. `--harness-cv` also runs the harness's default selection and reports what
it would have picked, with the validation bytes of that pick.

Objective per setting: model bytes + stored bytes of the validation records (stored units and,
for the raw-block method, the flag bitmap). Header and index are the same for every setting of
a method. Ties go to the smaller model, then to the earlier grid position, as in the harness.

One part of the grid is not searched in full. A zstd dictionary of kind `cover` is trained with
a parameter search that compresses the whole training input about 80 times at the level it is
trained for; at levels 19 and 22 that is about a minute of processor time per dictionary on
these training inputs, and the grid holds 90 of them per workload. For the zstd methods the
`cover` kind is therefore tried only at the (level, size) pairs of the `--cover-top` best
`fastcover` settings of that method (a mechanical rule, applied after the other kinds are
measured); the rest of the `cover` settings are counted as not tried. The DEFLATE grid, whose
dictionaries are all trained at level 3, is searched in full.

The output holds settings and byte counts only.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import freeze_common as F  # noqa: E402
from freeze_common import C, K  # noqa: E402


def date_utc() -> str:
    return subprocess.run(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'], capture_output=True, text=True).stdout.strip()


def zstd_configs(grid: dict, sizes: list[int]) -> list[dict]:
    """Same list, in the same order, as ZstdTunedCodec.train builds."""
    configs = [{'level': lv, 'dict_kind': 'none', 'dict_bytes_requested': 0} for lv in grid['zstd_levels']]
    configs += [{'level': lv, 'dict_kind': k, 'dict_bytes_requested': s}
                for k in grid['zstd_kinds'] for s in sizes for lv in grid['zstd_levels']]
    return configs


def deflate_configs(grid: dict, sizes: list[int]) -> list[dict]:
    """Same list, in the same order, as DeflateTunedCodec.train builds."""
    configs = [{'level': lv, 'dict_kind': 'none', 'dict_bytes_requested': 0} for lv in grid['deflate_levels']]
    configs += [{'level': lv, 'dict_kind': k, 'dict_bytes_requested': s}
                for k in grid['deflate_kinds'] for s in sizes for lv in grid['deflate_levels']]
    return configs


def rank(rows: list[dict]) -> list[dict]:
    ok = [r for r in rows if r['validation_objective_bytes'] is not None]
    ok.sort(key=lambda r: (r['validation_objective_bytes'], r['model_bytes'], r['grid_position']))
    return ok


def all_in(enc: C.EncodedUnits) -> dict:
    arc, acct = enc.pack(C.LANE_INDEX_WIDTH)
    return acct.as_dict()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--workload', required=True, choices=F.WORKLOADS)
    ap.add_argument('--train', required=True)
    ap.add_argument('--validation', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--fsst-src')
    ap.add_argument('--build-dir')
    ap.add_argument('--grid', default='full', choices=['full', 'quick'])
    ap.add_argument('--folds', type=int, default=4)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--harness-cv', action='store_true', help='also run the harness\'s own cross-validation selection')
    ap.add_argument('--cover-top', type=int, default=2,
                    help='per-record zstd methods: try `cover` at the (level, size) of this many best fastcover settings')
    ap.add_argument('--cover-top-blocks', type=int, default=0, help='the same for the small-block zstd methods')
    ap.add_argument('--methods', help='comma-separated subset (default: every tuned baseline)')
    args = ap.parse_args()

    native = F.load_native(args.fsst_src, args.build_dir)
    train, _ = F.load_custody_jsonl(args.train)
    val, _ = F.load_custody_jsonl(args.validation)
    ctx = K.TuneContext(native, train, folds=args.folds, seed=args.seed, grid=args.grid, groups=None)
    grid = ctx.grid
    train_bytes = sum(len(r) for r in train)
    wanted = set(args.methods.split(',')) if args.methods else None
    started = date_utc()
    t_start = time.perf_counter()

    out: dict = {
        'schema': 'short-record-decision/baseline-tuning/v1',
        'workload': args.workload,
        'started_utc': started,
        'objective': 'fit on the whole training input; model bytes + stored bytes of the validation records',
        'tie_break': 'smaller model, then earlier grid position',
        'cover_policy': {'per_record_zstd_methods_top': args.cover_top, 'small_block_zstd_methods_top': args.cover_top_blocks,
                         'rule': 'zstd `cover` dictionaries are tried only at the (level, size) pairs of this many best fastcover '
                                 'settings of the method; DEFLATE\'s grid is searched in full'},
        'grid': {'name': args.grid, **{k: v for k, v in grid.items()}},
        'inputs': {
            'train': {'records': len(train), 'bytes': train_bytes, 'sha256': F.sha256_file(args.train)},
            'validation': {'records': len(val), 'bytes': sum(len(r) for r in val), 'sha256': F.sha256_file(args.validation)},
        },
        'harness': {'zstd_library': native.zstd_version, 'zlib_library': native.zlib_version,
                    'reference_fsst_built': native.has_fsst, 'native_helper': native.facts},
        'methods': {},
    }

    def emit(name: str, body: dict) -> None:
        out['methods'][name] = body
        ch = body.get('chosen') or {}
        print(f'  {name:32s} chosen={ {k: ch.get(k) for k in F.SETTING_KEYS} }  all-in={body.get("validation_all_in", {}).get("total")}'
              f'  ({body.get("seconds")}s)', flush=True)

    # ---- raw
    if wanted is None or 'raw-indexed' in wanted:
        enc = K.RawCodec().encode(val)
        emit('raw-indexed', {'settings_tried': 0, 'chosen': None, 'validation_all_in': all_in(enc), 'seconds': 0})

    # ---- zstd, per record and in blocks
    for name, (framing, per_block) in F.ZSTD_METHODS.items():
        if wanted is not None and name not in wanted:
            continue
        t0 = time.perf_counter()
        codec = K.ZstdTunedCodec(native, framing, per_block)
        sizes = [s for s in grid['sizes'] if s <= train_bytes]
        all_cfgs = zstd_configs(grid, sizes)
        cover_top = args.cover_top if per_block == 1 else args.cover_top_blocks

        def measure_setting(pos: int, cfg: dict) -> dict:
            model = codec._fit(ctx, 'all', train, cfg)
            if model is None:
                return {**cfg, 'grid_position': pos, 'model_bytes': None, 'validation_stored_bytes': None,
                        'validation_objective_bytes': None}
            stored = codec._stored(model, val, cfg)
            return {**cfg, 'grid_position': pos, 'model_bytes': len(model[0]), 'validation_stored_bytes': stored,
                    'validation_objective_bytes': len(model[0]) + stored}

        rows = [measure_setting(pos, cfg) for pos, cfg in enumerate(all_cfgs) if cfg['dict_kind'] != 'cover']
        best_fast = rank([r for r in rows if r['dict_kind'] == 'fastcover'])[:max(0, cover_top)]
        cover_pairs = sorted({(r['level'], r['dict_bytes_requested']) for r in best_fast})
        cover_skipped = 0
        for pos, cfg in enumerate(all_cfgs):
            if cfg['dict_kind'] != 'cover':
                continue
            if (cfg['level'], cfg['dict_bytes_requested']) in cover_pairs:
                rows.append(measure_setting(pos, cfg))
            else:
                cover_skipped += 1
        ranked = rank(rows)
        best = ranked[0]
        pinned = F.PinnedZstd(native, framing, per_block, best)
        rep = pinned.train(train, ctx)
        body = {
            'settings_in_grid': len(all_cfgs), 'settings_tried': len(rows), 'settings_not_trainable': len(rows) - len(ranked),
            'cover_settings_not_tried': cover_skipped,
            'cover_tried_at_level_and_size': [list(x) for x in cover_pairs],
            'chosen': rep['chosen'], 'validation_all_in': all_in(pinned.encode(val)),
            'ranked': ranked, 'seconds': round(time.perf_counter() - t0, 1),
        }
        if args.harness_cv:
            t1 = time.perf_counter()
            cv = K.ZstdTunedCodec(native, framing, per_block)
            cv_rep = cv.train(train, ctx)
            body['harness_cross_validation'] = {
                'chosen': cv_rep['chosen'], 'best_5': cv_rep['best_5'], 'folds': cv_rep['folds'], 'fold_seed': cv_rep['fold_seed'],
                'validation_all_in': all_in(cv.encode(val)), 'seconds': round(time.perf_counter() - t1, 1),
            }
        emit(name, body)

    # ---- raw DEFLATE
    if wanted is None or 'deflate-raw-tuned' in wanted:
        t0 = time.perf_counter()
        codec = K.DeflateTunedCodec(native)
        sizes = [s for s in grid['sizes'] if s <= min(32768, train_bytes)]
        rows = []
        for pos, cfg in enumerate(deflate_configs(grid, sizes)):
            model = codec._fit(ctx, 'all', train, cfg)
            if model is None:
                rows.append({**cfg, 'grid_position': pos, 'model_bytes': None, 'validation_stored_bytes': None,
                             'validation_objective_bytes': None})
                continue
            stored = K._deflate_units(val, cfg['level'], model).stored_bytes()
            rows.append({**cfg, 'grid_position': pos, 'model_bytes': len(model), 'validation_stored_bytes': stored,
                         'validation_objective_bytes': len(model) + stored})
        ranked = rank(rows)
        pinned = F.PinnedDeflate(native, ranked[0])
        rep = pinned.train(train, ctx)
        body = {
            'settings_in_grid': len(rows), 'settings_tried': len(rows), 'settings_not_trainable': len(rows) - len(ranked),
            'chosen': rep['chosen'], 'validation_all_in': all_in(pinned.encode(val)),
            'ranked': ranked, 'seconds': round(time.perf_counter() - t0, 1),
        }
        if args.harness_cv:
            t1 = time.perf_counter()
            cv = K.DeflateTunedCodec(native)
            cv_rep = cv.train(train, ctx)
            body['harness_cross_validation'] = {
                'chosen': cv_rep['chosen'], 'best_5': cv_rep['best_5'], 'folds': cv_rep['folds'], 'fold_seed': cv_rep['fold_seed'],
                'validation_all_in': all_in(cv.encode(val)), 'seconds': round(time.perf_counter() - t1, 1),
            }
        emit('deflate-raw-tuned', body)

    # ---- reference FSST (no settings)
    if wanted is None or 'fsst-reference' in wanted:
        t0 = time.perf_counter()
        try:
            fs = F.HashedFsst(native)
            rep = fs.train(train, ctx)
            emit('fsst-reference', {'settings_tried': 0, 'chosen': rep['chosen'], 'validation_all_in': all_in(fs.encode(val)),
                                    'seconds': round(time.perf_counter() - t0, 1)})
        except K.NotApplicable as exc:
            emit('fsst-reference', {'status': 'not-applicable', 'reason': str(exc)})

    out['finished_utc'] = date_utc()
    out['elapsed_seconds'] = round(time.perf_counter() - t_start, 1)
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
    print(f'wrote {p.name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
