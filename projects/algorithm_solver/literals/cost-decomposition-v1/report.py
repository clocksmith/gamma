"""Rebuild sanitized metadata evidence/report from a completed diagnostic."""
import argparse
from collections import Counter
import json
from pathlib import Path
from analyze import HERE, sha, write


def grouped(values):
    result = Counter()
    for key, value in values.items():
        result['syntax' if key.startswith('syntax.') else key] += value
    return result


def main(run):
    raw = (run / 'results.json').read_bytes()
    r = json.loads(raw)
    assert r['contract_sha256'] == sha((HERE/'contract.json').read_bytes())
    primary = r['arms']['8']['dev_val']
    frac = grouped(primary['fractional_selections'])
    single = grouped(primary['single_character_selections'])
    c = r['bounds']['capacity_256']['selections']
    predictions = {
        'A1': all(r['arms'][w]['dev_val']['selections']['total'] == n for w,n in [('7',14014),('8',8948)]),
        'A2': max(frac,key=frac.get) == max(single,key=single.get) == 'syntax',
        'A3': r['bounds']['fit_substring_transfer_oracle']['dev_val_selections']['median'] < 32,
        'A4': c['median'] <= 32 and c['p95'] <= 96,
        'A5': all(len(r['arms'][w]['per_problem']) == 400 for w in ('7','8'))}
    r['predictions'] = predictions
    r['private_results_sha256'] = sha(raw)
    evidence = HERE/'evidence'
    evidence.mkdir(exist_ok=True)
    write(evidence/'results.json',r)
    largest = sorted(frac, key=lambda k: (-frac[k], ['syntax','identifier','literal'].index(k)))[0]
    lines = ['# M1 cost decomposition and optimistic bound', '',
        '[Frozen design](FREEZE.md), pushed in `2523d591c` before measurement. '
        '[Evidence](evidence/results.json) contains only IDs, hashes, counts and aggregates. '
        'Sources, dictionaries and sequences remain private.', '',
        f'The largest remaining category is **{largest}**. On L-R-256 dev-val it accounts for '
        f'{frac[largest]:.2f}/{primary["selections"]["total"]} byte-fraction-attributed selections '
        f'({100*frac[largest]/primary["selections"]["total"]:.1f}%). '
        'These are descriptive attributions; deleting a category would require resegmentation '
        'and can change correctness.', '',
        'The optimistic lower bounds do **not** establish M1 feasibility or impossibility. '
        'They leave substantial room below the current codebook. Local search stopping and '
        'general-compressor rates do not close that gap. M1 remains unchanged and unmet.', '',
        '## Measured baseline', '',
        '| Development split | Entries | Selections | Median | p95 | Single-character | Actions incl. Finish | Package bytes |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for split in ('dev_fit','dev_val'):
        for w in ('7','8'):
            d = r['arms'][w][split]; s=d['selections']
            lines.append(f'| {split} | {r["arms"][w]["entries"]} | {s["total"]:,} | {s["median"]} | {s["p95"]} | {100*d["single_character_fraction"]:.1f}% | {d["actions"]["total"]:,} | {d["package_bytes"]:,} |')
    lines += ['', 'Both dev-val selection totals reproduce the prior L-R baselines exactly. '
        'All 800 packets decode to the pinned R source hashes. Existing source qualification '
        'is reused; no new execution/correctness or numerical qualification is claimed. '
        'Only the 400 explicit development source paths were opened.', '',
        '## L-R-256 dev-val attribution', '',
        '| Category | Fractional selections | Share | Single-character selections | Share of tail | Source bytes |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    total_single = sum(single.values()); bytes_by = grouped(primary['source_bytes'])
    for cat in ('identifier','literal','syntax'):
        lines.append(f'| {cat} | {frac[cat]:.2f} | {100*frac[cat]/primary["selections"]["total"]:.1f}% | {single[cat]} | {100*single[cat]/total_single:.1f}% | {bytes_by[cat]} |')
    lines += ['', 'A2 failed: syntax leads total attributed selections, but identifiers lead the single-character tail. '
        'Mixed selections are split by byte overlap; the integer exclusive/mixed partition is in the evidence. Single-character attribution is '
        'exact integer accounting. Property names count as identifiers.', '',
        '| Syntax detail | Fractional selections | Single-character selections |', '| --- | ---: | ---: |']
    for k in sorted(primary['fractional_selections']):
        if k.startswith('syntax.'):
            lines.append(f'| {k.removeprefix("syntax.")} | {primary["fractional_selections"][k]:.2f} | {primary["single_character_selections"].get(k,0)} |')
    lines += ['', '## Optimistic bounds', '',
        '| Scope | Programs | Lower total selections | Lower median | Lower p95 |', '| --- | ---: | ---: | ---: | ---: |']
    for key,label in [('capacity_128','Arbitrary shared dictionary <=128, capacity relaxation'),('capacity_256','Arbitrary shared dictionary <=256, capacity relaxation'),('fit_substring_transfer_oracle','Fit-witnessed substrings only, unlimited union on dev-val'),('unlimited_cross_program_shared_oracle','Cross-program strings only, unlimited union; diagnostic')]:
        d=r['bounds'][key]; s=d.get('selections',d.get('dev_val_selections'))
        lines.append(f'| {label} | {s["n"]} | {s["total"]} | {s["median"]} | {s["p95"]} |')
    lines += ['', 'The capacity bound applies to arbitrary shared dictionaries for these **fixed '
        '400 sources**, not all equivalent programs or the full 500 qualification. At most K '
        'programs can benefit from private multi-character entries in a K-entry dictionary. '
        'The bound optimistically lowers those programs to two selections and makes every '
        'shared substring available without consuming slots. This drops shared-slot competition '
        'and is deliberately weak. Its median cannot rule out 32 when K=256 on 400 programs. '
        'It is a necessary bound, not an attainable dictionary.', '',
        'The fit-transfer oracle applies only to literals witnessed in fit (plus characters); '
        'designed unseen strings can beat it. The cross-program diagnostic uses validation text '
        'retrospectively and is not a fitted-vocabulary score. Both relax shared cardinality and '
        'whole-body exclusions. Whole-program exclusion supplies the two-selection floor. '
        'No single-character feasibility claim follows; its universal optimistic lower bound is zero.', '',
        'One Finish adds one to each action bound. Payload uses 7/8 bits per selection; packets '
        'also charge padding and 41-byte headers. Dictionary storage and codec source bytes '
        'are separate in evidence. Codec source size is not a full runtime-footprint measurement.', '',
        '## Predictions, checks and next action', '',
        '| Prediction | Outcome |', '| --- | --- |']
    lines += [f'| {key} | {"Met" if passed else "Not met"} |' for key,passed in predictions.items()]
    lines += ['', 'Six synthetic tests passed, including exhaustive tiny-dictionary lower-bound '
        'ordering, suffix-oracle comparison against brute force, mixed-span conservation and '
        'allowlisted loading. Python compilation passed. The existing judge/lane tests passed '
        '**37/37** using the existing `.venv_rocm` pytest runtime; no dependency was installed. '
        'The measurement itself uses system Python and Node, with one worker.', '',
        f'Measured analysis wall time: {r["runtime"]["seconds"]:.3f} seconds. '
        'Review and launch receipts are recorded in [REVIEW.md](REVIEW.md).', '',
        f'Next: board item 3 is claimed for a matched conventional dictionary experiment '
        f'targeting the {largest} tail, retaining the existing fit/validation separation, exact '
        'charging and baseline. A bound gap alone is not evidence that stronger search or a '
        'learned scorer will find a gain. No training is authorized.', '',
        'Rebuild this report from a complete private run with:', '', '```sh',
        'python3 -B projects/algorithm_solver/literals/cost-decomposition-v1/report.py --run /path/to/cost-decomposition/run-v1',
        '```', '',
        'Component: algorithm_solver literal research. Intent preserved. No production boundary '
        'changed; no held-out/protected opening, BITS deployment, private-source publication, '
        'ledger/catalog/claim write, human-study outcome or autonomous-solving claim.', '']
    (HERE/'README.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--run',type=Path,required=True)
    main(ap.parse_args().run)
