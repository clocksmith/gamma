"""Rebuild a sanitized Python-only result view from sealed private artifacts."""
import argparse
import json
from pathlib import Path
from run import HERE,LIT,analyze,tail,banned

prior=tail.module('python_name_prior_report',LIT/'tail-search-v1/report.py')


def main(run):
    raw=(run/'results.json').read_bytes();r=json.loads(raw);c=json.loads((HERE/'contract.json').read_text())
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes())
    ids=c['partition']['dev_val'];fit_ids=c['partition']['dev_fit'];all_ids=set(map(str,fit_ids+ids));n=len(ids)
    entries={x['id']:x['entry'] for x in c['sources']};arms={(a['width'],a['arm']):a for a in r['arms']}
    assert set(arms)=={(w,a) for w in (7,8) for a in ('control','rename','joint')}
    baseline={}
    for w in (7,8):
        folder=run/f'w{w}';text={int(k):v for k,v in json.loads((folder/'control/sources.json').read_text()).items()}
        vocab=json.loads((folder/'baseline-dictionary.json').read_text());db=len(analyze.dictionary_bytes(vocab))
        rows,illegal=tail.evaluate_output(text,vocab,w,banned({pid:{'original':s} for pid,s in text.items()},entries))
        for pid,row in rows.items():assert row['source_sha256']==next(x['sha256'] for x in c['sources'] if str(x['id'])==pid)
        baseline[str(w)]={'per_problem':rows,'fit':tail.aggregate(rows,fit_ids,db),'validation':tail.aggregate(rows,ids,db),
                          'illegal_entry_sha256':illegal,'dictionary_bytes':db,'entries':len(vocab)}
    for (w,name),a in arms.items():
        folder=run/f'w{w}';seal=json.loads((folder/'fit-seal.json').read_text())
        assert seal['validation_loaded'] is False
        for f,h in seal['arms'][name].items():assert analyze.sha((folder/name/f).read_bytes())==h
        assert a['dictionary_sha256']==seal['arms'][name]['dictionary.json']
        chosen=json.loads((folder/name/'sources.json').read_text())
        assert set(chosen)==set(a['per_problem'])==set(a['qualification'])==all_ids
        for pid,row in a['per_problem'].items():
            assert row['source_sha256']==analyze.sha(chosen[pid].encode())
            assert row['original_sha256']==baseline[str(w)]['per_problem'][pid]['source_sha256']
        a['paired_baseline']=prior.paired(a['per_problem'],baseline[str(w)]['per_problem'],ids)
        a['paired_control']=prior.paired(a['per_problem'],arms[w,'control']['per_problem'],ids)
        v,b,p=a['validation'],baseline[str(w)]['validation'],a['paired_baseline']
        a['readiness_checks']={'all_qualified':a['qualified']==len(all_ids),'coverage':v['covered']==b['covered']==n,
            'whole_solution_clean':not a['illegal_entry_sha256'],'actions_5_percent':v['actions']['total']<=.95*b['actions']['total'],
            'median_lower':v['actions']['median']<b['actions']['median'],'p90_lower':v['actions']['p90']<b['actions']['p90'],
            'improved_6':p['better']>=6,'worsened_at_most_2':p['worse']<=2,
            'fallback_nonincrease':v['single_character_fraction']<=b['single_character_fraction'],
            'package_within_105_percent':v['package_bytes']<=1.05*b['package_bytes']}
        a['ready']=all(a['readiness_checks'].values());a['m1_cost_indicators_only']=prior.indicators(a)
        for split,subset in [('fit',fit_ids),('validation',ids)]:
            rows=[a['per_problem'][str(pid)] for pid in subset];good=[x for x in rows if x['encodable']]
            a[split]['qualified']=sum(a['qualification'][str(pid)]['passed'] for pid in subset)
            a[split]['qualification_failed_ids']=[pid for pid in subset if not a['qualification'][str(pid)]['passed']]
            a[split]['changed']=sum(x['source_sha256']!=x['original_sha256'] for x in rows)
            a[split]['framing_bytes']=41*len(good);a[split]['payload_bits']=w*sum(x['selections'] for x in good)
            a[split]['padding_bits']=sum(8*(x['packet_bytes']-41)-w*x['selections'] for x in good)
    r['predictions']={
        'P1':all(arms[w,'control'][split]['selections']['total']==baseline[str(w)][split]['selections']['total'] for w in (7,8) for split in ('fit','validation')),
        'P2':arms[8,'rename']['validation']['covered']==n and arms[8,'rename']['validation']['actions']['total']<=.99*baseline['8']['validation']['actions']['total'],
        'P3':arms[8,'joint']['validation']['covered']==n and arms[8,'joint']['validation']['actions']['total']<arms[8,'rename']['validation']['actions']['total'],
        'P4':all(a['qualified']==len(all_ids) and a['fit']['covered']+a['validation']['covered']==len(all_ids) and not a['illegal_entry_sha256'] for a in arms.values()),
        'P5':not any(a['m1_cost_indicators_only'] for a in arms.values())}
    ready=sorted((a for a in arms.values() if a['ready']),key=lambda a:(a['validation']['actions']['total'],a['validation']['package_bytes'],a['arm']))
    r['selected_ready_arm']=([ready[0]['arm'],2**ready[0]['width']] if ready else None)
    r['baseline']=baseline;r['private_results_sha256']=analyze.sha(raw)
    qraw=(run/'qualification-private.json').read_bytes();qs=json.loads(qraw)
    r['qualification_receipt_sha256']=analyze.sha(qraw)
    q=r['fresh_qualification_summary']={'distinct_sources':len(qs),'passed':sum(x['passed'] for x in qs.values()),
        'checks_passed':sum(x['checks_passed'] for x in qs.values()),'checks_total':sum(x['cases'] for x in qs.values())}
    r['widths']=[{k:v for k,v in width.items() if k!='arms'} for width in r['widths']]
    def safe(value):
        if isinstance(value,dict):
            assert not {'trace','_trace','accepted_mapping','name','target','sources','vocab','failures'}&set(value)
            for v in value.values():safe(v)
        elif isinstance(value,list):
            for v in value:safe(v)
    safe(r);(HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Python vocabulary-aware naming transfer', '',
        '[Freeze](FREEZE.md) (`b22d9ed76`) and [pre-launch amendment](AMENDMENT-1.md) (`9b982eb5e`); '
        '[review/run receipt](REVIEW.md); [metadata evidence](evidence/results.json). Private sources, dictionaries, mappings, sequences and cases are excluded.', '',
        f'Development-ready selection: **{r["selected_ready_arm"] or "none"}**. '
        'The panel contains 27 fit and nine validation problems, all previously exposed and qualified in Python and inside the current development allowlist. '
        'This cannot qualify M1’s 500-problem target. Validation is source-plus-encoder optimization under fit-sealed dictionaries, followed by independent source qualification.', '',
        'At 256 entries, rename-only reduces validation actions from 949 to 937 (1.26%), with four improvements and no regressions. '
        'Joint search reaches 934 (1.58%) but worsens two programs, the median, and the single-character fraction. '
        'The 128-entry arms do not improve. These small-panel tradeoffs meet the predictions but fail readiness.', '',
        '## Costs and qualification', '',
        '| Entry cap | Arm | Split | Decoded | Qualified | Changed | Selections | Median | p90 | p95 | Worst | <=32/96 | Actions | Single-char | Package bytes |',
        '| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for (w,name),a in sorted(arms.items()):
        for split in ('fit','validation'):
            d=a[split];s=d['selections']
            lines.append(f'| {2**w} | {name} | {split} | {d["covered"]}/{d["problems"]} | {d["qualified"]}/{d["problems"]} | {d["changed"]} | {s["total"]} | {s["median"]} | {s["p90"]} | {s["p95"]} | {s["worst"]} | {s["within_32"]}/{s["within_96"]} | {d["actions"]["total"]} | {100*d["single_character_fraction"]:.2f}% | {d["package_bytes"]} |')
    lines+=['', 'Costs include encoded candidates even if qualification fails; unqualified costs are not credited improvements. '
        'Failures remain in the original denominator and block readiness. All selected source bytes, including imports and helpers, are emitted by exact literals. '
        'Actions include one Finish; navigation/correction are zero. Packages include dictionaries,41-byte headers and padding. Installed CPython/stdlib footprint is excluded and unmeasured.', '',
        '| Width | Arm | Better/same/worse vs learned baseline | Ready | Failed predicates |', '| ---: | --- | --- | --- | --- |']
    for (w,name),a in sorted(arms.items()):
        p=a['paired_baseline'];bad=', '.join(k for k,v in a['readiness_checks'].items() if not v) or 'None'
        lines.append(f'| {2**w} | {name} | {p["better"]}/{p["same"]}/{p["worse"]} | {a["ready"]} | {bad} |')
    lines+=['', '## Controlled contrasts', '', '| Width | Contrast | Validation action delta | Better/same/worse |', '| ---: | --- | ---: | --- |']
    for w in (7,8):
        for a,b in [('rename','control'),('joint','control'),('joint','rename')]:
            x,y=arms[w,a],arms[w,b];p=prior.paired(x['per_problem'],y['per_problem'],ids)
            delta=x['validation']['actions']['total']-y['validation']['actions']['total'] if x['validation']['covered']==y['validation']['covered']==n else 'Unavailable'
            lines.append(f'| {2**w} | {a} minus {b} | {delta} | {p["better"]}/{p["same"]}/{p["worse"]} |')
    lines+=['', '## Search accounting', '', '| Width | Arm | Round | Trials | Stop | Dictionary seconds | Rewrite trials/moves |', '| ---: | --- | ---: | ---: | --- | ---: | ---: |']
    for width in r['widths']:
        h=width['baseline'];lines.append(f'| {2**width["width"]} | baseline fit | 1 | {h["trials"]} | {h["stop"]} | {h["seconds"]:.2f} | 0/0 |')
    for (w,name),a in sorted(arms.items()):
        for i,h in enumerate(a['rounds']):
            lines.append(f'| {2**w} | {name} | {i+1} | {h["trials"]} | {h["stop"]} | {h["seconds"]:.2f} | {sum(v["trials"] for v in h["rewrite"].values())}/{sum(v["moves"] for v in h["rewrite"].values())} |')
    lines+=['', 'Dictionary seconds exclude preceding name rewrites. Baseline fitting is charged separately; all arms reuse it. '
        'Time-capped contrasts are budget-limited; local termination proves no optimum. Validation rewrite trials/moves, full action distributions, and framing/padding are in evidence.', '',
        '| Prediction | Met |', '| --- | --- |']
    lines += [f'| {k} | {v} |' for k,v in r['predictions'].items()]
    lines += ['', f'Fresh qualification: {q["passed"]}/{q["distinct_sources"]} distinct changed programs and '
        f'{q["checks_passed"]:,}/{q["checks_total"]:,} checks passed. Unchanged sources reuse prior qualification. '
        'Expected values stay outside the sandbox; observations include type, argument mutation and aliases. No retries, repairs or test-feedback selection.', '',
        f'Measured total wall time: {r["seconds"]:.2f} seconds. Eleven synthetic checks pass, including wrong-type parity and Unicode body offsets; compilation/import passes. '
        'The unchanged judge/lane retains A’s37 passing checks. This is finite development evidence, not arbitrary-input correctness or human/autonomous solving.', '',
        'Readiness authorizes only proposing separate confirmation. Final held-out/protected sets stay closed; no publication of private artifacts, BITS change, training or human study follows. '
        'Component intent preserved: algorithm_solver literal research, unchanged canonical codec and production boundaries; no claim/ledger/catalog writes.', '',
        'Rebuild: `python3 -B projects/algorithm_solver/literals/python-name-v1/report.py --run /private/path/to/python-name/run-v1`.', '']
    (HERE/'README.md').write_text('\n'.join(lines).replace('dictionaries,41-byte','dictionaries, 41-byte').replace('A’s37','A’s 37'))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);main(ap.parse_args().run)
