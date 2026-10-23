"""Rebuild sanitized results and replay sealed artifacts; never changes fitted choices."""
import argparse
import json
from pathlib import Path
from run import HERE,LIT,analyze,tail,e
p=tail.module('lns_names_metrics',LIT/'tail-search-v1/report.py')


def incremental(a,b,ids):
    v,s=a['validation'],b['validation'];pair=p.paired(a['per_problem'],b['per_problem'],ids)
    return {'qualified':all(q['passed'] for q in a['qualification'].values()),'coverage':v['covered']==100,
        'audits_clean':not a['illegal_entry_sha256'],'actions_lower':v['actions']['total']<s['actions']['total'],
        'median_nonincrease':v['actions']['median']<=s['actions']['median'],'p90_nonincrease':v['actions']['p90']<=s['actions']['p90'],
        'fallback_nonincrease':v['single_character_fraction']<=s['single_character_fraction'],
        'package_within_105_percent':v['package_bytes']<=1.05*s['package_bytes'],'worsened_at_most_25':pair['worse']<=25}


def main(folder):
    raw=(folder/'results.json').read_bytes();r=json.loads(raw);c=json.loads((HERE/'contract.json').read_text())
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes())
    hist=json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text());old={a['arm']:a for a in hist['arms'] if a['width']==8}
    arms={a['arm']:a for a in r['arms']};ids=c['partition']['dev_val'];expected={str(i) for group in c['partition'].values() for i in group}
    assert set(arms)=={f'{n}_{v}' for n in ('seed','ordinary','lns_fixed','lns_joint') for v in ('fixed_seed','adaptive')}
    assert json.loads((folder/'all-fit-sealed.json').read_text())['validation_loaded'] is False
    for name,a in arms.items():
        root=folder/'fit'/a['dictionary_arm'];private=folder/f'{name}-256';seal=json.loads((root/'fit-seal.json').read_text())
        assert not seal['validation_loaded']
        for file,digest in seal['files'].items():assert analyze.sha((root/file).read_bytes())==digest
        assert a['fit_search']['fit_seal_sha256']==analyze.sha((root/'fit-seal.json').read_bytes())
        vseal=json.loads((root/'validation-seal.json').read_text());assert not vseal['qualification_started']
        for file,digest in vseal['files'].items():assert analyze.sha((root/file).read_bytes())==digest
        assert a['validation_seal_sha256']==analyze.sha((root/'validation-seal.json').read_bytes())
        sources=json.loads((private/'sources.json').read_text());vocab=json.loads((private/'dictionary.json').read_text());db=(private/'dictionary.bin').read_bytes()
        assert analyze.sha((private/'dictionary.json').read_bytes())==a['dictionary_sha256']==seal['files']['dictionary.json']==vseal['dictionary_sha256']
        assert analyze.sha(db)==a['dictionary_binary_sha256'] and db==analyze.dictionary_bytes(vocab)
        assert set(sources)==set(a['per_problem'])==set(a['qualification'])==expected
        fit_sources=json.loads((root/'fit-sources.json').read_text())
        assert {str(i):sources[str(i)] for i in c['partition']['dev_fit']}==fit_sources
        assert a['fit']['selections']['total']==a['fit_search']['fit_selections']==seal['fit_selections']
        assert e.digest_texts({int(i):sources[str(i)] for i in ids})==vseal[a['view']+'_source_sha256']
        for pid,row in a['per_problem'].items():
            packet=(private/'packets'/f'{pid}.bin').read_bytes();text=sources[pid]
            assert analyze.decode(db,packet)==text and row['source_sha256']==analyze.sha(text.encode())
            assert row['original_sha256']==old['control']['per_problem'][pid]['source_sha256']
            assert packet==analyze.encode(vocab,analyze.shortest_encode(text,vocab),8)
            assert row['selections']==len(packet)-41
            row.update(source_bytes=len(text.encode()),packet_sha256=analyze.sha(packet),
                       one_program_package_bytes=len(db)+len(packet),one_program_with_decoder=len(db)+len(packet)+c['decoder_dependency_bytes'])
        for split,split_ids in [('fit',c['partition']['dev_fit']),('validation',ids)]:
            d=a[split];rows=[a['per_problem'][str(i)] for i in split_ids]
            d.update(source_bytes=sum(x['source_bytes'] for x in rows),single_character_codes=sum(x['single_characters'] for x in rows),
                     qualified=sum(a['qualification'][str(i)]['passed'] for i in split_ids),
                     changed=sum(x['source_sha256']!=x['original_sha256'] for x in rows),
                     package_with_decoder_dependencies=d['package_bytes']+c['decoder_dependency_bytes'],
                     framing_bytes=41*len(rows),payload_bits=8*sum(x['selections'] for x in rows),padding_bits=0)
            d['qualification_failed_ids']=[i for i in split_ids if not a['qualification'][str(i)]['passed']]
    # Compute decisions only after every arm has its qualification and cost fields.
    for name,a in arms.items():
        bases={'R':old['control'],'item13':old['scope_joint'],'seed_same_view':arms['seed_'+a['view']],'ordinary_same_view':arms['ordinary_'+a['view']]}
        a['paired']={k:p.paired(a['per_problem'],b['per_problem'],ids) for k,b in bases.items()}
        v,b=a['validation'],old['control']['validation'];pair=a['paired']['R']
        a['readiness_checks']={'qualified':all(q['passed'] for q in a['qualification'].values()),'coverage':v['covered']==100,
            'audits_clean':not a['illegal_entry_sha256'],'actions_5_percent':v['actions']['total']<=.95*b['actions']['total'],
            'median_lower':v['actions']['median']<b['actions']['median'],'p90_lower':v['actions']['p90']<b['actions']['p90'],
            'improved_60':pair['better']>=60,'worsened_at_most_25':pair['worse']<=25,
            'fallback_nonincrease':v['single_character_fraction']<=b['single_character_fraction'],
            'package_within_105_percent':v['package_bytes']<=1.05*b['package_bytes']}
        a['ready']=all(a['readiness_checks'].values())
        a['incremental_checks']={k:incremental(a,b,ids) for k,b in bases.items() if k!='R'}
        a['successor']=a['dictionary_arm'].startswith('lns_') and a['ready'] and all(all(q.values()) for q in a['incremental_checks'].values())
        a['m1_cost_indicators_only']=p.indicators(a)
    fit=lambda n:arms[n+'_fixed_seed']['fit']['selections']['total']
    r['predictions']={'J1':all(arms['seed_fixed_seed'][s]['selections']['total']==old['scope_joint'][s]['selections']['total'] for s in ('fit','validation')),
        'J2':all(fit(n)<=.99*fit('seed') for n in ('lns_fixed','lns_joint')),'J3':fit('lns_joint')<fit('lns_fixed'),
        'J4':any(arms[n+'_adaptive']['validation']['actions']['total']<=.99*arms['ordinary_adaptive']['validation']['actions']['total'] for n in ('lns_fixed','lns_joint')),
        'J5':all(a['qualified']==400 and a['fit']['covered']+a['validation']['covered']==400 and not a['illegal_entry_sha256'] for a in arms.values()),
        'J6':any(a['successor'] for a in arms.values())}
    winners=sorted((a for a in arms.values() if a['successor']),key=lambda a:(a['validation']['actions']['total'],a['validation']['package_bytes'],a['dictionary_arm'],a['view']))
    r['selected_successor']=winners[0]['arm'] if winners else None;r['private_results_sha256']=analyze.sha(raw)
    r['decoder_dependency_bytes']=c['decoder_dependency_bytes'];r['offline_encoder_bytes']=c['offline_encoder_bytes'];r['offline_encoder_scope']=c['offline_encoder_scope']
    qs=json.loads((folder/'qualification-private.json').read_text());r['qualification_receipt_sha256']=analyze.sha((folder/'qualification-private.json').read_bytes())
    r['fresh_qualification_summary']={'distinct_sources':len(qs),'passed':sum(q['passed'] for q in qs.values()),'checks_passed':sum(q['checks_passed'] for q in qs.values()),'checks_total':sum(q['cases'] for q in qs.values())}
    def clean(value):
        if isinstance(value,dict):
            assert not {'_trace','trace','accepted_colors','vocab','sources','tokens','failures','changes','name','target','args'}&set(value)
            for x in value.values():clean(x)
        elif isinstance(value,list):
            for x in value:clean(x)
    clean(r);(HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Exact dictionary repairs with per-binding naming','','[Freeze](FREEZE.md); [review/run receipt](REVIEW.md); [evidence](evidence/results.json). Private sources, dictionaries, packets, cases and repair traces remain private.','',
        f'Selected incremental successor: **{r["selected_successor"] or "none"}**. This is adaptive consumed-development evidence, not independent confirmation, autonomous assembly or M1 qualification.','',
        'All dictionaries start from item13 scope_joint256. Ordinary and lns_joint alternate naming with dictionary fitting; lns_fixed preserves fit source bytes. Every dictionary gets a fixed item13 validation view and a common two-call naming view. Only LNS candidates passing readiness against R and incremental checks against item13, seed and ordinary under the same view can be selected.','',
        '| Arm | Split | Decoded/qualified | Selections | Median/p90/p95/worst | <=32/96 | Actions | Character codes/fraction | Raw package | With decoder sources |',
        '| --- | --- | --- | ---: | --- | --- | ---: | --- | ---: | ---: |']
    for name,a in arms.items():
        for split in ('fit','validation'):
            d=a[split];s=d['selections'];lines.append(f'| {name} | {split} | {d["covered"]}/{d["qualified"]} | {s["total"]} | {s["median"]}/{s["p90"]}/{s["p95"]}/{s["worst"]} | {s["within_32"]}/{s["within_96"]} | {d["actions"]["total"]} | {d["single_character_codes"]}/{100*d["single_character_fraction"]:.2f}% | {d["package_bytes"]} | {d["package_with_decoder_dependencies"]} |')
    lines+=['','One Finish, complete dictionary, 41-byte frame and eight-bit selections charged. Decoder source storage is separate; the offline solver/runtime installation is not a complete measured deployment footprint. Every failed choice remains in its denominator.','',
        '| Arm | Comparator | Action delta | Better/same/worse | Failed incremental checks |','| --- | --- | ---: | --- | --- |']
    fail=lambda d:', '.join(k for k,v in d.items() if not v) or 'None'
    for name,a in arms.items():
        for base,pair in a['paired'].items():
            b=old['control' if base=='R' else 'scope_joint'] if base in ('R','item13') else arms[('seed_' if base=='seed_same_view' else 'ordinary_')+a['view']]
            lines.append(f'| {name} | {base} | {a["validation"]["actions"]["total"]-b["validation"]["actions"]["total"]} | {pair["better"]}/{pair["same"]}/{pair["worse"]} | {fail(a["incremental_checks"][base]) if base!="R" else "See readiness below"} |')
    lines+=['','| Arm | Ready vs R | Incremental successor | Failed readiness |','| --- | --- | --- | --- |']
    for name,a in arms.items():lines.append(f'| {name} | {a["ready"]} | {a["successor"]} | {fail(a["readiness_checks"])} |')
    lines+=['','| Dictionary arm | Round | Before/naming/repair/polish selections | Accepted/attempted repairs | Repair stop/seconds | Polish trials/stop |','| --- | ---: | --- | --- | --- | --- |']
    for name in ('ordinary','lns_fixed','lns_joint'):
        for h in arms[name+'_fixed_seed']['fit_search']['rounds']:
            rep=h['repair'];pol=h['polish'];accepted=sum(m['accepted'] for m in rep['moves']) if rep else 0
            lines.append(f'| {name} | {h["round"]+1} | {h["before"]}/{h["after_naming"]}/{h["after_repair"]}/{h["after_polish"]} | {accepted}/{len(rep["moves"]) if rep else 0} | {str(rep["stop"])+"/"+format(rep["seconds"],".2f") if rep else "None"} | {pol["trials"]}/{pol["stop"]} |')
    lines+=['','Each MILP optimizes a bounded candidate pool for the selected source snapshot; it does not optimize all retained variants jointly. Exact rescoring and source reselection are recorded separately. Solver status0 is solver-reported optimality of that repair, not an independently certified global optimum. Time-limited feasible solutions are candidates only. LNS receives additional compute beyond ordinary continuation.','',
        '| Prediction | Met |','| --- | --- |']+[f'| {k} | {v} |' for k,v in r['predictions'].items()]
    q=r['fresh_qualification_summary'];lines+=['',f'Distinct final changed sources: {q["passed"]}/{q["distinct_sources"]} qualified, {q["checks_passed"]}/{q["checks_total"]} strict original-case/parity checks. All choices sealed before execution, no retries or repairs. Unchanged R reuses its pinned receipt. Finite reused development cases do not establish universal equivalence. Measured run wall time: {r["seconds"]:.2f} seconds.','',
        'Component intent preserved; canonical codec and production behavior unchanged. Confirmation, protected data, training, publication, deployment and human studies remain owner-gated. Private selected artifacts: lns-naming/run-v1/<selected>-256. No ledger/catalog/claim writes.','',
        'Rebuild with the pinned SciPy Python: `python -B projects/algorithm_solver/literals/lns-naming-v1/report.py --run /private/lns-naming/run-v1`.','']
    (HERE/'README.md').write_text('\n'.join(lines))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);main(ap.parse_args().run)
