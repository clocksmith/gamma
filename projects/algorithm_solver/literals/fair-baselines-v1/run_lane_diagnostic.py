#!/usr/bin/env python3
"""Diagnostic: the lane's short and medium suites, measured with independent baselines.

    python3 run_lane_diagnostic.py --work-dir <directory outside the repository> \
        --fsst-src <checkout of github.com/cwida/fsst> --check-with-lane-code

Question asked: on the short-record suites of `../rung2-short-ra-bench-v1`, is BIT3's size lead
over zstd explained by zstd's per-record frame bytes, and does the reference FSST change the
FSST comparison?

This is a diagnostic, not a decision test. The held-out halves of these suites were already
used while the lane's codec was designed. BIT3 numbers are copied from the lane's committed
results file; BIT3 is not run here.

The suite records come from other repositories and are written only under --work-dir.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fb_core as C  # noqa: E402
import fb_measure as M  # noqa: E402
import lane_suites as L  # noqa: E402
from fb_candidate import load_candidate  # noqa: E402
from run_fair_baselines import add_common_args, load_native_from_args, options_from_args, summary_rows  # noqa: E402

LANE_RESULTS = HERE.parent / 'rung2-short-ra-bench-v1' / 'results' / 'ra_pareto_benchmark_v1.json'
LANE_NAMES = {'BIT3': 'BIT3', 'FSST-255': 'FSST-255 (lane\'s own implementation)',
              'DFL3-raw-zdict': 'DEFLATE raw + dictionary', 'ZST3-tuned': 'zstd -19 full frame + dictionary'}
REPRODUCTION = {'ZST3-tuned': 'zstd-frame-lane-rule', 'DFL3-raw-zdict': 'deflate-raw-lane-rule',
                'FSST-255': 'fsst-lane-own-impl'}


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _fmt(v, nd=0):
    if v is None:
        return ''
    if isinstance(v, float):
        return f'{v:,.{nd}f}'
    return f'{v:,}'


def suite_tables(label: str, entry: dict) -> str:
    lane = entry['lane_committed']
    bit3 = lane['BIT3']['held_out_bytes']
    rows = entry['harness']['summary']
    out = [f'### `{label}`', '']
    rb, cm = entry['rebuilt_totals'], entry['committed_totals']
    out.append(f'Records rebuilt today: train {rb["train_docs"]} records / {rb["train_raw_bytes"]:,} B, held-out '
               f'{rb["held_out_docs"]} records / {rb["held_out_raw_bytes"]:,} B. Committed run: train '
               f'{cm["train_raw_bytes"]:,} B, held-out {cm["held_out_raw_bytes"]:,} B. '
               + ('The totals match.' if entry['rebuilt_matches_committed_totals'] else
                  '**The totals differ: the source files changed after the committed run, so the rebuilt suite is '
                  'not the same record set.**'))
    out += ['', 'Lane, committed (its own run, its own record set):', '',
            '| codec | held-out bytes | vs BIT3 | ns/seek |', '|---|---:|---:|---:|']
    for key, name in LANE_NAMES.items():
        c = lane[key]
        out.append(f'| {name} | {c["held_out_bytes"]:,} | {c["held_out_bytes"] - bit3:+,} | {c["ns_per_seek"]:,.0f} |')
    out += ['', 'This harness, per-record methods (rebuilt record set):', '',
            '| method | like-for-like bytes | vs BIT3 committed | all-in | all-in, compact index | model | index | framing | payload | ns/lookup | median ns | p95 ns |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        if r.get('table') == 'blocks':
            continue
        if r['status'] != 'ok':
            out.append(f'| {r["method"]} | {r["status"].upper()} | | | | | | | | | | |')
            continue
        note = '' if r['timing_kind'] == 'native-loop' else ' (Python loop)'
        out.append(
            f'| {r["method"]} | {_fmt(r["like_for_like_lane_form"])} | {r["like_for_like_lane_form"] - bit3:+,} | '
            f'{_fmt(r["all_in"])} | {_fmt(r["all_in_compact_index"])} | {_fmt(r["model"])} | {_fmt(r["index"])} | '
            f'{_fmt(r["framing"])} | {_fmt(r["payload"])} | {_fmt(r["loop_mean_ns"], 1)}{note} | '
            f'{_fmt(r["per_record_median_ns"], 1)} | {_fmt(r["per_record_p95_ns"], 1)} |')
    out += ['', 'This harness, small compressed blocks (zstd lean frame per block of N records):', '',
            '| method | like-for-like bytes | vs BIT3 committed | all-in | model | index | framing | payload | raw bytes decoded per lookup (mean) | ns/lookup | p95 ns |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        if r.get('table') != 'blocks':
            continue
        if r['status'] != 'ok':
            out.append(f'| {r["method"]} | {r["status"].upper()} | | | | | | | | | |')
            continue
        out.append(
            f'| {r["method"]} | {_fmt(r["like_for_like_lane_form"])} | {r["like_for_like_lane_form"] - bit3:+,} | '
            f'{_fmt(r["all_in"])} | {_fmt(r["model"])} | {_fmt(r["index"])} | {_fmt(r["framing"])} | '
            f'{_fmt(r["payload"])} | {_fmt(r["mean_raw_bytes_decoded_per_lookup"], 1)} | {_fmt(r["loop_mean_ns"], 1)} | '
            f'{_fmt(r["per_record_p95_ns"], 1)} |')
    rep = entry['reproduction']
    out += ['', 'Reproduction check (same rule as the lane, rebuilt record set):', '',
            '| lane codec | lane committed | this harness, lane rule | difference |', '|---|---:|---:|---:|']
    for key, r in rep.items():
        out.append(f'| {LANE_NAMES[key]} | {_fmt(r["lane_committed_bytes"])} | {_fmt(r["this_harness_bytes"])} | '
                   f'{"" if r["difference"] is None else format(r["difference"], "+,")} |')
    out.append('')
    return '\n'.join(out)


def framing_analysis(entry: dict) -> dict:
    """Numbers that bear on the framing question, with what each one rests on."""
    lane = entry['lane_committed']
    bit3, zst3 = lane['BIT3']['held_out_bytes'], lane['ZST3-tuned']['held_out_bytes']
    by = {m['name']: m for m in entry['harness']['methods'] if m['status'] == 'ok'}

    def lfl(name):
        return by[name]['bytes']['like_for_like_lane_form'] if name in by else None

    out = {'bit3_committed': bit3, 'lane_zstd_committed': zst3, 'lane_gap_zstd_minus_bit3': zst3 - bit3}
    rule = by.get('zstd-frame-lane-rule')
    if rule:
        fr = rule['bytes']['all_in']['framing']
        out['zstd_lane_rule_rebuilt'] = {
            'like_for_like_bytes': lfl('zstd-frame-lane-rule'),
            'framing_bytes_measured': fr,
            'frame_header_bytes': rule['detail']['frame_header_bytes'],
            'block_header_bytes': rule['detail']['block_header_bytes'],
            'framing_bytes_per_record_min_max': rule['detail']['framing_bytes_per_record_min_max'],
            'like_for_like_minus_framing': lfl('zstd-frame-lane-rule') - fr,
        }
        out['lane_zstd_committed_minus_measured_framing'] = {
            'bytes': zst3 - fr,
            'minus_bit3_committed': zst3 - fr - bit3,
            'rests_on': 'framing measured on the rebuilt records (13 bytes per record under 256 bytes, 14 above) '
                        'subtracted from the lane\'s committed zstd number; assumes the block contents stay the same',
        }
    out['vs_bit3_committed'] = {
        name: {'like_for_like_bytes': lfl(name), 'minus_bit3_committed': lfl(name) - bit3}
        for name in ('zstd-frame-tuned', 'zstd-lean-frame-tuned', 'zstd-raw-block-tuned',
                     'zstd-lean-frame-tuned/per-group', 'zstd-raw-block-tuned/per-group', 'deflate-raw-tuned',
                     'deflate-raw-tuned/per-group', 'fsst-reference', 'fsst-reference/per-group',
                     'fsst-lane-own-impl', 'raw-indexed') if lfl(name) is not None
    }
    smallest = min(((v['like_for_like_bytes'], k) for k, v in out['vs_bit3_committed'].items()), default=None)
    if smallest:
        out['smallest_per_record_baseline'] = {'method': smallest[1], 'like_for_like_bytes': smallest[0],
                                               'minus_bit3_committed': smallest[0] - bit3}
    if lfl('fsst-reference') is not None and lfl('fsst-lane-own-impl') is not None:
        out['fsst_reference_minus_lane_impl_same_records'] = lfl('fsst-reference') - lfl('fsst-lane-own-impl')
    out['caveat'] = ('"minus_bit3_committed" compares baselines on the rebuilt record set with BIT3 on the committed '
                     'record set; see rebuilt_matches_committed_totals and the reproduction block for how far apart '
                     'the two sets are')
    return out


def analysis_lines(a: dict) -> list[str]:
    out = ['Framing question:', '']
    out.append(f'- Lane, committed: zstd {a["lane_zstd_committed"]:,} B, BIT3 {a["bit3_committed"]:,} B, gap {a["lane_gap_zstd_minus_bit3"]:+,} B.')
    r = a.get('zstd_lane_rule_rebuilt')
    if r:
        lo, hi = r['framing_bytes_per_record_min_max']
        out.append(f'- Measured framing in the lane-style zstd archive (rebuilt records): {r["framing_bytes_measured"]:,} B '
                   f'({r["frame_header_bytes"]:,} frame header incl. magic, {r["block_header_bytes"]:,} block header; {lo} to {hi} B per record).')
        c = a['lane_zstd_committed_minus_measured_framing']
        out.append(f'- Lane zstd committed minus that framing: {c["bytes"]:,} B, which is {c["minus_bit3_committed"]:+,} B against BIT3 committed.')
    s = a.get('smallest_per_record_baseline')
    if s:
        out.append(f'- Smallest per-record baseline here: `{s["method"]}` at {s["like_for_like_bytes"]:,} B, {s["minus_bit3_committed"]:+,} B against BIT3 committed.')
    if 'fsst_reference_minus_lane_impl_same_records' in a:
        out.append(f'- Reference FSST minus the lane\'s FSST on the same records: {a["fsst_reference_minus_lane_impl_same_records"]:+,} B.')
    out.append('')
    return out


def _cell_bytes(row: dict | None, bit3: int) -> str:
    if row is None:
        return ''
    if row['status'] != 'ok':
        return row['status'].upper()
    v = row['like_for_like_lane_form']
    return f'{v:,} ({v - bit3:+,})'


def _cell_time(row: dict | None) -> str:
    if row is None or row['status'] != 'ok' or row.get('loop_mean_ns') is None:
        return ''
    cell = f'{row["loop_mean_ns"]:,.0f} / {row["per_record_median_ns"]:,.0f} / {row["per_record_p95_ns"]:,.0f}'
    return cell if row['timing_kind'] == 'native-loop' else cell + ' (Python loop)'


def render_markdown(report: dict) -> str:
    suites = report['suites']
    labels = list(suites)
    rows_by = {lab: {r['method']: r for r in suites[lab]['harness']['summary']} for lab in labels}
    methods = [r['method'] for r in suites[labels[0]]['harness']['summary']]
    bit3 = {lab: suites[lab]['lane_committed']['BIT3']['held_out_bytes'] for lab in labels}
    head = '| | ' + ' | '.join(f'`{lab}`' for lab in labels) + ' |'
    rule = '|---|' + '---:|' * len(labels)
    out = ['# Lane suites diagnostic', '',
           'Diagnostic only. The held-out halves of these suites were already used during the lane\'s design. '
           'BIT3 numbers are copied from the lane\'s committed results; BIT3 was not run.', '',
           f'Records: {report["records_source"]}.', '',
           '## Sizes', '',
           'Like-for-like bytes (the lane\'s container form), with the difference from BIT3\'s committed number '
           'in brackets. The baselines were measured on the rebuilt record sets; where a rebuilt set differs from '
           'the committed one (see the per-suite notes), the bracketed difference is across two record sets.', '',
           head, rule]
    out.append('| held-out records, raw bytes (rebuilt) | ' + ' | '.join(
        f'{suites[lab]["rebuilt_totals"]["held_out_docs"]}, {suites[lab]["rebuilt_totals"]["held_out_raw_bytes"]:,}' for lab in labels) + ' |')
    out.append('| held-out records, raw bytes (committed run) | ' + ' | '.join(
        f'{suites[lab]["committed_totals"]["held_out_docs"]}, {suites[lab]["committed_totals"]["held_out_raw_bytes"]:,}' for lab in labels) + ' |')
    for key, name in LANE_NAMES.items():
        out.append(f'| lane, committed: {name} | ' + ' | '.join(
            f'{suites[lab]["lane_committed"][key]["held_out_bytes"]:,} '
            f'({suites[lab]["lane_committed"][key]["held_out_bytes"] - bit3[lab]:+,})' for lab in labels) + ' |')
    for m in methods:
        out.append(f'| this harness: `{m}` | ' + ' | '.join(_cell_bytes(rows_by[lab].get(m), bit3[lab]) for lab in labels) + ' |')
    loads = ', '.join(f'{suites[lab]["harness"]["timer"].get("load_average_1m_at_end")}' for lab in labels)
    out += ['', '## Lookup time', '',
            'Nanoseconds per single-record lookup, in memory, same loop for every method: loop mean (best round) / '
            'median of per-record means / 95th percentile of per-record means. '
            f'One-minute load average of the machine when each suite finished: {loads}. '
            'The lane\'s committed ns/seek come from its own loop on another occasion and are listed only for reference.', '',
            head, rule]
    for key, name in LANE_NAMES.items():
        out.append(f'| lane, committed (mean only): {name} | ' + ' | '.join(
            f'{suites[lab]["lane_committed"][key]["ns_per_seek"]:,.0f}' for lab in labels) + ' |')
    for m in methods:
        out.append(f'| this harness: `{m}` | ' + ' | '.join(_cell_time(rows_by[lab].get(m)) for lab in labels) + ' |')
    out += ['', '## Per suite', '']
    for lab in labels:
        out.append(suite_tables(lab, suites[lab]))
        out += analysis_lines(suites[lab]['framing_analysis'])
    return '\n'.join(out) + '\n'


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--work-dir', help='directory outside the repository for the rebuilt suite records')
    ap.add_argument('--render-only', action='store_true', help='rewrite the tables from an existing --out file and stop')
    ap.add_argument('--workspace-root', default=str(L.DEFAULT_WORKSPACE_ROOT),
                    help='directory holding the repositories the lane samples from')
    ap.add_argument('--suites', default=','.join(L.DEFAULT_SUITES))
    ap.add_argument('--check-with-lane-code', action='store_true',
                    help='also run the lane\'s own sampler in a child process and compare pool digests')
    ap.add_argument('--reuse-exported', action='store_true',
                    help='measure the suite records already under --work-dir instead of sampling the workspace again')
    ap.add_argument('--out', default=str(HERE / 'results' / 'lane_suites_diagnostic_v1.json'))
    add_common_args(ap)
    args = ap.parse_args()

    if args.render_only:
        out = Path(args.out)
        out.with_suffix('.md').write_text(render_markdown(json.loads(out.read_text(encoding='utf-8'))), encoding='utf-8')
        print(f'rewrote {out.with_suffix(".md").name}')
        return 0
    if not args.work_dir:
        ap.error('--work-dir is required')
    work = Path(args.work_dir)
    if _inside(work, HERE.parents[3]):
        print('refusing: --work-dir must be outside the repository (suite records are not ours to commit)', file=sys.stderr)
        return 2
    labels = [s for s in args.suites.split(',') if s]
    native, fsst_src = load_native_from_args(args)
    opts = options_from_args(args)
    candidates = [load_candidate(spec) for spec in args.candidate]

    pool_names = sorted({p for lab in labels for p in L.SUITES[lab][:2]})
    loaded: dict[str, tuple[C.RecordSet, C.RecordSet]] = {}
    my_digests: dict[str, str] = {}
    if not args.reuse_exported:
        print('sampling pools ...')
        pools = L.build_pools(Path(args.workspace_root), pool_names)
    for label in labels:
        sdir = work / 'suites' / label
        if not args.reuse_exported:
            suite = L.suite_records(pools, label)
            if sdir.exists():
                shutil.rmtree(sdir)
            L.export_suite(suite, sdir)
        train, test = C.load_records(sdir / 'train'), C.load_records(sdir / 'test')
        if not args.reuse_exported:
            assert train.records == [r for _, r in suite['train']] and test.records == [r for _, r in suite['test']]
        loaded[label] = (train, test)
        for k, pool in enumerate(L.SUITES[label][:2]):
            group = f'{k + 1}-{pool}'
            members = [r for rs in (train, test) for r, g in zip(rs.records, rs.groups) if g == group]
            my_digests[pool] = L.pool_digest(members)
    lane_check: dict = {'run': bool(args.check_with_lane_code),
                        'compares': 'pool digests of the measured records with the lane\'s own sampler run now'}
    if args.check_with_lane_code:
        try:
            theirs = L.digests_from_lane_code(pool_names)
            lane_check.update(equal={n: theirs.get(n) == my_digests[n] for n in pool_names},
                              all_equal=all(theirs.get(n) == my_digests[n] for n in pool_names))
        except Exception:
            lane_check.update(error='the lane sampler could not be run in a child process')
        print('lane sampler check:', lane_check)

    committed = {s['label']: s for s in json.loads(LANE_RESULTS.read_text(encoding='utf-8'))['suites']}
    entries = {}
    for label in labels:
        print(f'\n== {label}')
        train, test = loaded[label]
        doc = M.run(native, train, test, opts, candidates=candidates, fsst_src=fsst_src, progress=print)
        doc['summary'] = summary_rows(doc)
        com = committed[label]
        rebuilt_totals = {'train_docs': len(train), 'held_out_docs': len(test),
                          'train_raw_bytes': train.total_bytes, 'held_out_raw_bytes': test.total_bytes}
        committed_totals = {k: com[k] for k in rebuilt_totals}
        by_name = {m['name']: m for m in doc['methods']}
        reproduction = {}
        for lane_key, mine in REPRODUCTION.items():
            m = by_name.get(mine)
            got = m['bytes']['like_for_like_lane_form'] if m and m['status'] == 'ok' else None
            reproduction[lane_key] = {
                'this_harness_method': mine,
                'lane_committed_bytes': com['codecs'][lane_key]['held_out_bytes'],
                'this_harness_bytes': got,
                'difference': None if got is None else got - com['codecs'][lane_key]['held_out_bytes'],
                'lane_committed_setting': {k: v for k, v in com['codecs'][lane_key].items()
                                           if k in ('tuned_maxdict', 'tuned_dict_kind', 'dict_bytes', 'symbols')},
                'this_harness_setting': (m or {}).get('tuning', {}).get('chosen'),
            }
        entries[label] = {
            'rebuilt_totals': rebuilt_totals,
            'committed_totals': committed_totals,
            'rebuilt_matches_committed_totals': rebuilt_totals == committed_totals,
            'pool_digests': {p: my_digests[p] for p in L.SUITES[label][:2]},
            'lane_committed': com['codecs'],
            'reproduction': reproduction,
            'harness': doc,
        }
        entries[label]['framing_analysis'] = framing_analysis(entries[label])

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    report = {
        'schema': 'fair-baselines-lane-diagnostic/v1',
        'command': [M.public_arg(a) for a in ['python3', Path(sys.argv[0]).name, *sys.argv[1:]]],
        'status': 'diagnostic only: the held-out halves of these suites were already used during the lane\'s design',
        'bit3_source': 'BIT3 numbers are copied from ../rung2-short-ra-bench-v1/results/ra_pareto_benchmark_v1.json; BIT3 was not run',
        'records_source': ('suite records exported by an earlier run of this script (--reuse-exported)'
                           if args.reuse_exported else 'sampled from the workspace by this run'),
        'lane_sampler_check': lane_check,
        'suites': entries,
    }
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    md_path = out.with_suffix('.md')
    md_path.write_text(render_markdown(report), encoding='utf-8')
    print(f'\nwrote {out.name} and {md_path.name} in {out.parent.name}/')
    bad = [f'{lab}:{m["name"]}' for lab, e in entries.items() for m in e['harness']['methods']
           if m['status'] in ('failed-verification', 'error')]
    if bad:
        print('methods that failed:', bad)
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
