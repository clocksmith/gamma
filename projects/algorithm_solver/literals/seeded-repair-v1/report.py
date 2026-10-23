"""Rebuild matched diagnostics by replaying sealed models and canonical packets."""
import argparse
import hashlib
import json
from pathlib import Path
import model as m
HERE=m.HERE;LIT=m.LIT;analyze=m.analyze


def main(folder,work):
    raw=(folder/'results.json').read_bytes();r=json.loads(raw);c=json.loads((HERE/'contract.json').read_text())
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes()) and not r['validation_loaded']
    for rel,h in c['private_files'].items():assert analyze.sha((work/rel).read_bytes())==h
    texts=json.loads((work/c['seed_relative_path']/'fit-sources.json').read_text());seed=json.loads((work/c['seed_relative_path']/'dictionary.json').read_text())
    seal=json.loads((folder/'all-snapshots-sealed.json').read_text());assert seal['before_solver_calls'] and not seal['validation_loaded']
    assert analyze.sha((folder/'pool.json').read_bytes())==r['pool_sha256']
    import sys
    sys.path.insert(0,str(LIT/'character-slots-v1'))
    spec=m.importlib.util.spec_from_file_location('seeded_report_slots',LIT/'character-slots-v1/run.py');slots=m.importlib.util.module_from_spec(spec);spec.loader.exec_module(slots)
    banned=slots.sel.forbidden_strings(texts)
    for pair in r['pairs']:
        root=folder/f'trial-{pair["trial"]:02d}';snapshot=json.loads((root/'snapshot.json').read_text())
        assert analyze.sha((root/'snapshot.json').read_bytes())==pair['snapshot_sha256']==seal['snapshot_hashes'][pair['trial']]
        built=m.build(texts,snapshot['fixed'],snapshot['candidates'],snapshot['capacity'],seed);matrix=built['matrix'];h=hashlib.sha256()
        for array in (matrix.indptr,matrix.indices,matrix.data,built['lower'],built['upper'],built['cost'],built['start']):h.update(array.tobytes())
        assert h.hexdigest()==pair['model_sha256'] and built['initial']==pair['initial'];del built,matrix
        for a in pair['runs']:
            assert a['model_sha256']==pair['model_sha256'] and not a['validation_loaded']
            if not a['feasible']:assert a['decoded']==0 and a['exact'] is None;continue
            private=root/('warm' if a['warm'] else 'cold');vocab=json.loads((private/'dictionary.json').read_text());db=(private/'dictionary.bin').read_bytes()
            assert analyze.sha((private/'dictionary.json').read_bytes())==a['dictionary_sha256'] and db==analyze.dictionary_bytes(vocab)
            assert len(vocab)==len(set(vocab))<=256 and set(snapshot['fixed'])<=set(vocab) and not set(vocab)&banned
            assert set(vocab)<=set(snapshot['fixed'])|set(snapshot['candidates']) and len(set(vocab)-set(snapshot['fixed']))<=snapshot['capacity']
            assert set(a['per_problem'])==set(texts)
            for pid,row in a['per_problem'].items():
                seq=analyze.shortest_encode(texts[pid],vocab);packet=(private/'packets'/f'{pid}.bin').read_bytes()
                assert analyze.decode(db,packet)==texts[pid] and packet==analyze.encode(vocab,seq,8) and analyze.sha(packet)==row['packet_sha256']
                assert analyze.sha(texts[pid].encode())==row['source_sha256'] and len(seq)==row['selections']
                assert row['characters']==sum(len(vocab[k])==1 for k in seq)
                row['one_program_with_decoder']=row['one_program_package_bytes']+c['decoder_dependency_bytes']
            rows=list(a['per_problem'].values());n=sum(x['selections'] for x in rows);assert n==a['exact']
            assert n<=a['objective']+1e-6 and (not a['optimal'] or abs(n-a['objective'])<=1e-6)
            a.update(selections=analyze.distribution([x['selections'] for x in rows]),actions=analyze.distribution([x['actions'] for x in rows]),
                     character_codes=sum(x['characters'] for x in rows),character_fraction=sum(x['characters'] for x in rows)/n,
                     framing_bytes=41*len(rows),payload_bits=8*n,padding_bits=0,package_with_decoder_sources=a['package_bytes']+c['decoder_dependency_bytes'],
                     amortized_package_bytes=a['package_bytes']/len(rows),body_audit_clean=True)
        cold=next(a for a in pair['runs'] if not a['warm']);warm=next(a for a in pair['runs'] if a['warm']);both=cold['feasible'] and warm['feasible']
        pair.update(exact_delta=warm['exact']-cold['exact'] if both else None,
                    warm_feasibility_advantage=warm['feasible'] and not cold['feasible'],warm_feasibility_regression=cold['feasible'] and not warm['feasible'],
                    complete_call_delta_seconds=warm['call_seconds']-cold['call_seconds'],
                    retained_incumbent_delta=min(pair['initial'],warm['exact'] if warm['feasible'] else pair['initial'])-min(pair['initial'],cold['exact'] if cold['feasible'] else pair['initial']))
    summary={}
    for group in ('all','fixed96','optional'):
        pairs=[p for p in r['pairs'] if group=='all' or p['mode']==group];q={}
        for name in ('cold','warm'):
            rows=[a for p in pairs for a in p['runs'] if a['warm']==(name=='warm')]
            q[name]={'calls':len(rows),'feasible':sum(a['feasible'] for a in rows),'nonworse':sum(a['nonworse'] for a in rows),
                     'improves':sum(a['improves'] for a in rows),'optimal':sum(a['optimal'] for a in rows),
                     'call_seconds':sum(a['call_seconds'] for a in rows),'solver_run_seconds':sum(a['solver_run_seconds'] for a in rows),
                     'decoded':sum(a['decoded'] for a in rows),'feasible_exact_sum':sum(a['exact'] for a in rows if a['feasible']),
                     'cost_sum_scope':'Sum of independent300-program model outputs, not one shared dictionary; partial if any call lacks a feasible point.'}
        q.update(paired_better=sum(p['exact_delta'] is not None and p['exact_delta']<0 for p in pairs),
                 paired_same=sum(p['exact_delta']==0 for p in pairs),paired_worse=sum(p['exact_delta'] is not None and p['exact_delta']>0 for p in pairs),
                 unavailable_pairs=sum(p['exact_delta'] is None for p in pairs),feasibility_advantages=sum(p['warm_feasibility_advantage'] for p in pairs),
                 feasibility_regressions=sum(p['warm_feasibility_regression'] for p in pairs),
                 retained_better=sum(p['retained_incumbent_delta']<0 for p in pairs),retained_same=sum(p['retained_incumbent_delta']==0 for p in pairs),retained_worse=sum(p['retained_incumbent_delta']>0 for p in pairs))
        summary[group]=q
    s=summary['all'];allrows=[a for p in r['pairs'] for a in p['runs']]
    r['predictions']={'W1':s['warm']['feasible']==s['warm']['nonworse']==8,'W2':s['paired_better']>=4,'W3':s['warm']['improves']>=6,
        'W4':s['warm']['optimal']>s['cold']['optimal'],'W5':all(p['start_checked'] for p in r['pairs']) and all(not a['feasible'] or a['decoded']==300 and a['body_audit_clean'] for a in allrows),
        'W6':s['warm']['call_seconds']<=1.05*s['cold']['call_seconds']}
    r['recommend_for_future_frozen_search']=r['predictions']['W1'] and r['predictions']['W5'] and s['paired_better']+s['feasibility_advantages']>0 and s['paired_worse']==s['feasibility_regressions']==0
    r.update(summary=summary,private_results_sha256=analyze.sha(raw),decoded_packets=sum(a['decoded'] for a in allrows),decoder_dependency_bytes=c['decoder_dependency_bytes'],offline_encoder_bytes=c['offline_encoder_bytes'],offline_encoder_scope=c['offline_encoder_scope'])
    def clean(x):
        if isinstance(x,dict):
            assert not {'vocab','sources','candidates','fixed','cases','args','failures','start','matrix'}&set(x)
            for value in x.values():clean(value)
        elif isinstance(x,list):
            for value in x:clean(value)
    clean(r);(HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Known-incumbent initialization for exact repairs','','[Freeze](FREEZE.md); [review/run receipt](REVIEW.md); [metadata evidence](evidence/results.json). Models, start vectors, dictionaries, sources and packets remain private.','',
        f'Recommend for a future frozen search: **{r["recommend_for_future_frozen_search"]}**. Warm/cold paired exact costs: {s["paired_better"]} better, {s["paired_same"]} same, {s["paired_worse"]} worse, {s["unavailable_pairs"]} unavailable. No candidate promotion, validation or M1 claim.','',
        f'Post-hoc search-incumbent attribution: after each condition retains the better of the supplied seed and its returned dictionary, warm is {s["retained_better"]} better, {s["retained_same"]} same and {s["retained_worse"]} worse. Returning a better nonimproving solver point does not improve the existing search incumbent. This additional attribution leaves frozen W1–W6 and the tool-recommendation rule unchanged.','',
        'Eight snapshots start independently from the same item13 source/dictionary seed. Every pair shares one hashed model, objective, candidate order, budget and solver options. Only warm receives the algebraically checked complete incumbent. Order is balanced; calls run sequentially on the same core. No prior frozen search is rerun or revised.','',
        '| Trial/type | Order | Cold exact / flow objective | Warm exact / flow objective | Warm−cold exact | Cold/warm optimal | Cold/warm call seconds |','| --- | --- | --- | --- | ---: | --- | --- |']
    for p in r['pairs']:
        cold=next(a for a in p['runs'] if not a['warm']);warm=next(a for a in p['runs'] if a['warm'])
        lines.append(f'| {p["trial"]}/{p["mode"]} | {"warm first" if p["runs"][0]["warm"] else "cold first"} | {cold["exact"]}/{cold["objective"]} | {warm["exact"]}/{warm["objective"]} | {p["exact_delta"] if p["exact_delta"] is not None else "Unavailable"} | {cold["optimal"]}/{warm["optimal"]} | {cold["call_seconds"]:.2f}/{warm["call_seconds"]:.2f} |')
    lines+=['','Exact cost independently re-encodes the chosen dictionary and can be below a time-limited feasible flow objective. Solver optimality concerns only that bounded repair model; it is not a global vocabulary certificate. Missing feasible points remain failed calls with no invented cost.','',
        '| Group | Condition | Feasible/nonworse/improving/optimal | Calls | Complete call / solver seconds | Decoded |','| --- | --- | --- | ---: | --- | ---: |']
    for group,q in summary.items():
        for name in ('cold','warm'):
            z=q[name];lines.append(f'| {group} | {name} | {z["feasible"]}/{z["nonworse"]}/{z["improves"]}/{z["optimal"]} | {z["calls"]} | {z["call_seconds"]:.2f}/{z["solver_run_seconds"]:.2f} | {z["decoded"]} |')
    lines+=['','Per-result selection/action quantiles, character counts/fractions, dictionary/packet and one-program/amortized costs are in evidence. Each is an independent300-program dictionary result: their summed costs are a matched diagnostic, not a new shared vocabulary. Every encoded program pays one Finish, eight-bit selections,41-byte frame and full dictionary storage. Decoder source inventory is separately charged; full runtime footprint is unmeasured.','',
        '| Prediction | Met |','| --- | --- |']+[f'| {k} | {v} |' for k,v in r['predictions'].items()]
    lines+=['',f'{r["decoded_packets"]} packets independently decode; total wall time {r["seconds"]:.2f} seconds. Start feasibility/model hashes are rebuilt without solving during reporting. Four synthetic tests include32exhaustive comparisons against both direct conditions and SciPy, plus zero-time incumbent retention. Source qualification reuses item15 by exact hash; no case rerun. Item23 failure remains unchanged.','',
        'The version-pinned internal HiGHS binding is research-local. Component intent and canonical decoder preserved; no production API, training, protected opening, source publication, ledger/catalog/claim write, deployment or human study.','',
        'Rebuild with pinned SciPy Python: `python -B projects/algorithm_solver/literals/seeded-repair-v1/report.py --run /private/seeded-repair/run-v1 --work /private/literal-admission500-v1`.','']
    (HERE/'README.md').write_text('\n'.join(lines))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);a=ap.parse_args();main(a.run,a.work)
