#!/usr/bin/env python3
# UNFINISHED. Part of a short-record-decision freeze that was paused before FREEZE.json was written.
# Nothing here is pinned. See ../FREEZE-PROGRESS.md for what was run, what was never run, and the next steps.
"""Is the adapter the lane's codec? Compare it with the lane's own scripts on the same records.

    python3 -B check_adapter_fidelity.py --export <old-suite-export dir> --out adapter-fidelity-old-suites.json

For each exported suite of the lane's old benchmark (`<suite>/<train|test>/<group>/<NNNN>.bin`):

  lane     the lane's own functions, run in a child process on these records:
             run_ra_pareto_bench.evaluate_suite            -> BIT3 `held_out_bytes`
             evaluate_transfer_vmm_2x2.evaluate_suite_2x2  -> `held_out_ra_bytes` per generator and cell
  adapter  bits_adapter.Bit3Candidate through the harness's `measure` (fit on train, encode test,
           every record decoded alone in random order by the Python reader and by the C reader)

Both numbers are the length of one self-contained BIT3 archive of the held-out records. They
should be equal, byte for byte, when the adapter calls the lane's code the way the lane does.

One thing can make them differ without any fault in the adapter. The lane's scripts give
engine.c a wall-clock limit of 8 seconds and use whatever chain exists when it runs out; on
a busy machine that chain is shorter, and the lane's own numbers then change from run to run.
The adapter refuses a chain the limit cut short. Here both sides get a limit long enough for
the search to complete where the lane's functions take one as an argument
(`evaluate_suite_2x2`); `run_ra_pareto_bench.evaluate_suite` has its 8 seconds built in, so a
difference in its row is checked by running again on a quieter machine before it is read as
a difference in the codec.

These suites' held-out halves were used while the codec was designed. Nothing here is evidence
about unseen data; the check is about the adapter only. The output holds counts, no content.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
LITERALS = next(p for p in HERE.parents if (p / 'fair-baselines-v1').is_dir())

SHORT_SUITES = ('short_wgsl_vs_json_80_to_80', 'short_ts_vs_mjs_80_to_80')
ALL_SUITES = SHORT_SUITES + ('med_ts_vs_json_50_to_50',)
VMM_ARMS = ('bpe', 'greedy-byte', 'greedy-entry', 'union_bpe_ge')
VMM_CELLS = ('base_vmm', 'revival_only_vmm', 'loo_only_vmm', 'transfer_vmm')
ADAPTER_ENGINE_LIMIT_SEC = 3600.0
LANE_2X2_ENGINE_LIMIT_SEC = 600.0   # the lane's own main() passes 8.0 for these suites


def date_utc() -> str:
    return subprocess.run(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'], capture_output=True, text=True).stdout.strip()


def load_suite(export: Path, label: str):
    import freeze_common as F
    train = F.C.load_records(export / label / 'train')
    test = F.C.load_records(export / label / 'test')
    return train, test


def halves(rs):
    labels = []
    for g in rs.groups:
        if not labels or labels[-1] != g:
            labels.append(g)
    assert len(labels) == 2, 'expected two contiguous groups'
    return ([r for r, g in zip(rs.records, rs.groups) if g == labels[0]],
            [r for r, g in zip(rs.records, rs.groups) if g == labels[1]])


def lane_child(export: Path, label: str, with_vmm: bool) -> dict:
    """Runs the lane's own scripts. Kept in a separate process from the adapter."""
    for d in ('codenet-replication-v1', 'rung2-presearch-v1', 'rung2-short-ra-bench-v1', 'rung3-archive-search-v1', 'rung3-vmm-subset-v1'):
        sys.path.insert(0, str(LITERALS / d))
    import run_ra_pareto_bench as RA
    from equal_budget_eval import compile_engine
    train, test = load_suite(export, label)
    tr1, tr2 = halves(train)
    te1, te2 = halves(test)
    out: dict = {'train_records': len(train), 'held_out_records': len(test), 'held_out_raw_bytes': test.total_bytes}
    with tempfile.TemporaryDirectory(prefix='fidelity-bins-') as tmp:
        bdir = Path(tmp)
        c_bench = RA.compile_c_bench(bdir)
        eng = compile_engine(bdir)
        ra = RA.evaluate_suite(c_bench, eng, label=label, train_1=tr1, train_2=tr2, test_1=te1, test_2=te2)
        b = ra['codecs']['BIT3']
        out['run_ra_pareto_bench'] = {'layout_used': b['layout_used'], 'selected_entries': b['selected_entries'],
                                      'held_out_bytes': b['held_out_bytes'], 'in_sample_bytes': b['in_sample_bytes'],
                                      'other_codecs_held_out_bytes': {k: v['held_out_bytes'] for k, v in ra['codecs'].items() if k != 'BIT3'}}
        if with_vmm:
            import evaluate_transfer_vmm_2x2 as E2
            x2 = E2.evaluate_suite_2x2(eng, c_bench, label=label, train_1=tr1, train_2=tr2, test_1=te1, test_2=te2,
                                       k_max=1024, limit_sec=LANE_2X2_ENGINE_LIMIT_SEC)
            out['evaluate_transfer_vmm_2x2'] = {
                arm: {cell: {'entries': res[cell]['entries'], 'held_out_ra_bytes': res[cell]['held_out_ra_bytes']}
                      for cell in VMM_CELLS}
                for arm, res in x2['generators'].items()}
    return out


def adapter_side(export: Path, label: str, with_vmm: bool, native) -> dict:
    import bits_adapter as A
    import freeze_common as F
    import fb_measure as M
    from fb_candidate import CandidateAdapter
    train, test = load_suite(export, label)
    opts = M.Options(per_group=False, timing=False)
    ctx = F.K.TuneContext(native, train.records, folds=opts.folds, seed=opts.seed, grid=opts.grid, groups=train.groups)

    def one(cfg: dict) -> dict:
        cand = A.Bit3Candidate(cfg)
        m = M.measure(native, cand.name, lambda: CandidateAdapter(cand), train, test, ctx, opts)
        if m['status'] != 'ok':
            return {'status': m['status'], 'reason': m.get('reason') or m.get('verification')}
        return {'status': 'ok', 'held_out_bytes': m['bytes']['all_in']['total'],
                'entries': m['tuning']['dictionary_entries'], 'layout_used': m['tuning']['layout_used'],
                'k_max_used': m['tuning']['k_max_used'],
                'verified': {k: v.get('ok') for k, v in m['verification'].items() if isinstance(v, dict)},
                'unseen_single_bytes_added': cand.last_encode_report.get('unseen_single_bytes_added')}

    out = {'mdl_prefix_stop_lane_rule': one({'layout': 'lane-predictor', 'k_max': 'lane-predictor', 'arm': 'greedy-entry',
                                             'selection': 'mdl_prefix_stop', 'engine_limit_sec': ADAPTER_ENGINE_LIMIT_SEC})}
    if with_vmm:
        out['vmm_two_tables_k1024'] = {
            arm: {cell: one({'layout': 'B', 'k_max': 1024, 'arm': arm, 'selection': cell, 'engine_limit_sec': ADAPTER_ENGINE_LIMIT_SEC})
                  for cell in VMM_CELLS}
            for arm in VMM_ARMS}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--export', required=True, help='directory holding the exported old suites')
    ap.add_argument('--out')
    ap.add_argument('--suites', default=','.join(ALL_SUITES))
    ap.add_argument('--lane-child', help=argparse.SUPPRESS)
    ap.add_argument('--with-vmm', action='store_true', help=argparse.SUPPRESS)
    args = ap.parse_args()
    export = Path(args.export)

    if args.lane_child:
        res = lane_child(export, args.lane_child, args.with_vmm)
        print('FIDELITY-JSON ' + json.dumps(res))
        return 0

    import freeze_common as F
    native = F.load_native()
    doc = {'schema': 'short-record-decision/adapter-fidelity/v1', 'started_utc': date_utc(),
           'note': 'old suites, held-out halves already used in design: a check of the adapter, not of the codec',
           'load_average_1m_at_start': round(os.getloadavg()[0], 2), 'suites': {}}
    worst = 0
    for label in [s for s in args.suites.split(',') if s]:
        with_vmm = label in SHORT_SUITES
        cmd = [sys.executable, '-B', str(Path(__file__).resolve()), '--export', str(export), '--lane-child', label]
        if with_vmm:
            cmd.append('--with-vmm')
        proc = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith('FIDELITY-JSON ')), None)
        if proc.returncode != 0 or line is None:
            tail = (proc.stderr.strip().splitlines() or ['no output'])[-1]
            doc['suites'][label] = {'lane': {'status': 'error', 'reason': tail[:300]}}
            print(f'{label}: the lane\'s script failed: {tail[:300]}')
            continue
        lane = json.loads(line[len('FIDELITY-JSON '):])
        mine = adapter_side(export, label, with_vmm, native)
        rows = []
        a = mine['mdl_prefix_stop_lane_rule']
        rows.append({'configuration': 'MDL prefix stop, layout and budget from the lane\'s predictor (run_ra_pareto_bench)',
                     'lane_bytes': lane['run_ra_pareto_bench']['held_out_bytes'], 'adapter_bytes': a.get('held_out_bytes'),
                     'lane_entries': lane['run_ra_pareto_bench']['selected_entries'], 'adapter_entries': a.get('entries'),
                     'adapter_status': a['status'], 'adapter_verified': a.get('verified'), 'adapter_reason': a.get('reason')})
        if with_vmm:
            for arm in VMM_ARMS:
                for cell in VMM_CELLS:
                    la = lane['evaluate_transfer_vmm_2x2'][arm][cell]
                    ad = mine['vmm_two_tables_k1024'][arm][cell]
                    rows.append({'configuration': f'{cell}, seed chain {arm}, K 1024, two tables (evaluate_transfer_vmm_2x2)',
                                 'lane_bytes': la['held_out_ra_bytes'], 'adapter_bytes': ad.get('held_out_bytes'),
                                 'lane_entries': la['entries'], 'adapter_entries': ad.get('entries'),
                                 'adapter_status': ad['status'], 'adapter_verified': ad.get('verified'),
                                 'adapter_reason': ad.get('reason')})
        for r in rows:
            r['difference_bytes'] = (r['adapter_bytes'] - r['lane_bytes']) if r['adapter_bytes'] is not None else None
            if r['difference_bytes'] is None:
                worst = max(worst, 1 << 30)
            else:
                worst = max(worst, abs(r['difference_bytes']))
            print(f'{label:30s} {r["configuration"][:70]:70s} lane {r["lane_bytes"]:7d}  adapter {str(r["adapter_bytes"]):>7s}  diff {r["difference_bytes"]}')
        doc['suites'][label] = {
            'held_out_records': lane['held_out_records'], 'held_out_raw_bytes': lane['held_out_raw_bytes'],
            'lane_predictor_layout': lane['run_ra_pareto_bench']['layout_used'],
            'lane_other_codecs_held_out_bytes': lane['run_ra_pareto_bench']['other_codecs_held_out_bytes'],
            'rows': rows,
        }
    doc['largest_absolute_difference_bytes'] = worst
    doc['finished_utc'] = date_utc()
    doc['load_average_1m_at_end'] = round(os.getloadavg()[0], 2)
    if args.out:
        Path(args.out).write_text(json.dumps(doc, indent=1) + '\n', encoding='utf-8')
        print(f'wrote {Path(args.out).name}')
    return 0 if worst == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
