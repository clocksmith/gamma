"""Report completed fixed-source search; private strings never enter this view."""
import argparse
from collections import Counter
import json
from pathlib import Path
from search import HERE, LIT, analyze


def paired(rows, reference, ids):
    counts = Counter(better=0, same=0, worse=0, failed=0)
    for pid in ids:
        a, b = rows[str(pid)], reference[str(pid)]
        if not a.get('encodable', True):
            counts['failed'] += 1
            counts['worse'] += 1
        elif not b.get('encodable', True):
            counts['better'] += 1
        else:
            delta = a['actions'] - b['actions']
            counts['better' if delta < 0 else 'worse' if delta > 0 else 'same'] += 1
    return dict(counts)


def indicators(arm):
    v = arm['validation']
    return (v['covered'] == v['problems'] and not arm['illegal_entry_sha256']
            and v['selections']['median'] <= 32 and v['selections']['p95'] <= 96
            and v['single_character_fraction'] <= .10)


def main(run):
    raw = (run/'results.json').read_bytes()
    r = json.loads(raw)
    assert r['contract_sha256'] == analyze.sha((HERE/'contract.json').read_bytes())
    parent = json.loads((LIT/'cost-decomposition-v1/contract.json').read_text())
    baseline = json.loads((LIT/'cost-decomposition-v1/evidence/results.json').read_text())
    ids = parent['partition']['dev_val']
    arms = {(a['width'], a['arm']): a for a in r['arms']}
    assert set(arms) == {(w,n) for w in (7,8) for n in ('control','alphabet','positions','joint')}
    expected_ids = {str(p) for s in parent['partition'].values() for p in s}
    for (w,n), a in arms.items():
        assert set(a['per_problem']) == expected_ids
        for pid, row in a['per_problem'].items():
            assert row['source_sha256'] == baseline['arms'][str(w)]['per_problem'][pid]['source_sha256']
        seal = json.loads((run/f'{n}-{2**w}'/'fit-seal.json').read_text())
        assert seal['validation_loaded'] is False and seal['dictionary_sha256'] == a['dictionary_sha256']
        assert analyze.sha((run/f'{n}-{2**w}'/'dictionary.json').read_bytes()) == a['dictionary_sha256']
        a['fit_seal_sha256'] = analyze.sha((run/f'{n}-{2**w}'/'fit-seal.json').read_bytes())
        b = baseline['arms'][str(w)]
        a['paired_baseline'] = paired(a['per_problem'], b['per_problem'], ids)
        a['paired_control'] = paired(a['per_problem'], arms[w,'control']['per_problem'], ids)
        v, bv, p = a['validation'], b['dev_val'], a['paired_baseline']
        a['readiness_checks'] = dict(
            coverage=v['covered'] == len(ids), whole_solution_clean=not a['illegal_entry_sha256'],
            actions_5_percent=v['actions']['total'] <= .95*bv['actions']['total'],
            median_lower=v['actions']['median'] < bv['actions']['median'],
            p90_lower=v['actions']['p90'] < bv['actions']['p90'],
            improved_60=p['better'] >= 60, worsened_at_most_25=p['worse'] <= 25,
            fallback_nonincrease=v['single_character_fraction'] <= bv['single_character_fraction'],
            package_within_105_percent=v['package_bytes'] <= 1.05*bv['package_bytes'])
        a['ready'] = all(a['readiness_checks'].values())
        a['m1_cost_indicators_only'] = indicators(a)
        for split, split_ids in [('fit',parent['partition']['dev_fit']),('validation',ids)]:
            rows = [a['per_problem'][str(pid)] for pid in split_ids if a['per_problem'][str(pid)]['encodable']]
            a[split]['framing_bytes'] = 41*len(rows)
            a[split]['payload_bits'] = w*sum(x['selections'] for x in rows)
            a[split]['padding_bits'] = sum(8*(x['packet_bytes']-41)-w*x['selections'] for x in rows)
            a[split]['dictionary_bytes'] = a['dictionary_bytes']
    predictions = {
        'T1': all(arms[w,'control']['fit']['selections']['total'] <= baseline['arms'][str(w)]['dev_fit']['selections']['total'] and abs(arms[w,'control']['validation']['selections']['total']/baseline['arms'][str(w)]['dev_val']['selections']['total']-1)<.01 for w in (7,8)),
        'T2': all(arms[w,'alphabet']['validation']['covered'] == 100 and arms[w,'alphabet']['validation']['actions']['total'] <= factor*baseline['arms'][str(w)]['dev_val']['actions']['total'] for w,factor in ((7,.97),(8,.99))),
        'T3': any(0 < 1-arms[w,'positions']['fit']['selections']['total']/baseline['arms'][str(w)]['dev_fit']['selections']['total'] < .05 for w in (7,8)),
        'T4': arms[8,'joint']['validation']['covered'] == 100 and all(arms[8,'joint']['validation']['actions']['total'] < arms[8,n]['validation']['actions']['total'] for n in ('alphabet','positions')),
        'T5': all(a['fit']['covered']+a['validation']['covered'] == 400 and not a['illegal_entry_sha256'] for a in arms.values()),
        'T6': not any(indicators(a) for a in arms.values())}
    ready = sorted((a for a in arms.values() if a['ready']), key=lambda a:(a['validation']['actions']['total'],a['validation']['package_bytes'],a['arm']))
    r.update(predictions=predictions, selected_ready_arm=([ready[0]['arm'],2**ready[0]['width']] if ready else None),
             private_results_sha256=analyze.sha(raw), baseline_evidence_sha256=analyze.sha((LIT/'cost-decomposition-v1/evidence/results.json').read_bytes()))
    (HERE/'evidence').mkdir(exist_ok=True)
    analyze.write(HERE/'evidence/results.json',r)
    lines = ['# Tail search: alphabet and all-position proposals', '',
        '[Freeze](FREEZE.md) pushed as `4a409954b`; [review and run receipt](REVIEW.md). '
        '[Evidence](evidence/results.json) contains counts, IDs and hashes. Private source strings, dictionaries and sequences are excluded.', '',
        f'Development-ready selection: **{r["selected_ready_arm"] or "none"}**. '
        'Readiness is only for a separately proposed confirmation. M1 qualification, unseen generalization and deployment are not established.', '',
        'The searched controls reproduce the pinned baselines. Reclaiming seven alphabet slots leaves three validation programs unencodable at both widths. '
        'The full-coverage positions arm adds 16 validation actions at 128 and saves only five at 256; its single-character fraction increases at both widths. '
        'No arm passes readiness. All searches stop locally before either cap; none is time-limited.', '',
        '## Fixed-source results', '',
        '| Width | Arm | Split | Covered | Selections | Median | p90 | p95 | Worst | <=32 / <=96 | Actions | Single-char | Package bytes |',
        '| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for (w,n),a in sorted(arms.items()):
        for split in ('fit','validation'):
            d=a[split]; s=d['selections']
            lines.append(f'| {2**w} | {n} | {split} | {d["covered"]}/{d["problems"]} | {s["total"]} | {s["median"]} | {s["p90"]} | {s["p95"]} | {s["worst"]} | {s["within_32"]} / {s["within_96"]} | {d["actions"]["total"]} | {100*d["single_character_fraction"]:.2f}% | {d["package_bytes"]} |')
    lines += ['', 'All numeric cost summaries use encodable rows; failed IDs remain in the coverage denominator, count as regressions and block readiness. '
        'Every successful packet independently decoded to its pinned source hash. Source bytes are unchanged; prior semantic qualification is reused. '
        'Complete actions add one Finish. Navigation/correction actions are zero. Packages include dictionaries, 41-byte packet headers and padding; runtime storage is unmeasured.', '',
        '## Paired validation and search limits', '',
        '| Width | Arm | Better/same/worse vs baseline | Better/same/worse vs searched control | Failed | Trials | Stop | Seconds | Ready |',
        '| ---: | --- | --- | --- | ---: | ---: | --- | ---: | --- |']
    for (w,n),a in sorted(arms.items()):
        p,q=a['paired_baseline'],a['paired_control']
        lines.append(f'| {2**w} | {n} | {p["better"]}/{p["same"]}/{p["worse"]} | {q["better"]}/{q["same"]}/{q["worse"]} | {p["failed"]} | {a["trials"]} | {a["stop"]} | {a["seconds"]:.2f} | {a["ready"]} |')
    lines += ['', 'Contrasts involving a time-capped arm are budget-limited. All arms are bounded searches; local termination does not establish an optimum. '
        'The alphabet factor reclaims seven fit-unused character slots; the positions factor changes proposals only. '
        'Exact whole-source dynamic programming accepts moves. These conventional search results do not authorize a learned scorer.', '',
        '## Factorial contrasts', '',
        '| Width | Contrast | Full-validation action delta | Common covered IDs | Action delta on common IDs | Fit selection delta |', '| ---: | --- | ---: | ---: | ---: | ---: |']
    for w in (7,8):
        for a,b in [('alphabet','control'),('positions','control'),('joint','control'),('joint','alphabet'),('joint','positions')]:
            x,y=arms[w,a],arms[w,b]
            common=[str(pid) for pid in ids if x['per_problem'][str(pid)]['encodable'] and y['per_problem'][str(pid)]['encodable']]
            delta=sum(x['per_problem'][pid]['actions']-y['per_problem'][pid]['actions'] for pid in common)
            lines.append(f'| {2**w} | {a} minus {b} | {delta if len(common)==100 else "Unavailable"} | {len(common)} | {delta} | {x["fit"]["selections"]["total"]-y["fit"]["selections"]["total"]} |')
    lines += ['', 'Negative deltas mean fewer selections/actions. Interpret totals only alongside coverage; an encoding failure is not a saving. '
        'Per-arm syntax/identifier/literal fractional attribution and single-character counts, complete action distributions, header/padding totals, and each readiness predicate are in the evidence.', '',
        '## Predictions and verification', '', '| Prediction | Met |', '| --- | --- |']
    lines += [f'| {k} | {v} |' for k,v in predictions.items()]
    lines += ['', f'Measured total wall time: {r["seconds"]:.2f} seconds. '
        'Six synthetic search checks and compilation passed before launch. A’s 37 passing judge/lane tests apply to unchanged infrastructure; no new source-execution campaign was needed. '
        'Fit dictionaries were sealed before opening validation; the report verifies the seals and source hashes. Final held-out 100 and protected 66 remain closed.', '',
        'Next: board item 4, vocabulary-aware source rewriting, needs a separate freeze and fresh qualification of changed programs. '
        'No training, human study, source publication or live-profile change is authorized by these results.', '',
        'Component: algorithm_solver literal research. Intent preserved; production boundaries and decoder semantics unchanged. No ledger/catalog/claim writes.', '',
        'Rebuild: `python3 -B projects/algorithm_solver/literals/tail-search-v1/report.py --run /private/path/to/tail-search/run-v1`.', '']
    (HERE/'README.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--run',type=Path,required=True)
    main(ap.parse_args().run)
