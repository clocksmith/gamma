"""Replay sealed packets and rebuild metadata-only results; never fit or repair."""
import argparse
import json
import sys
from pathlib import Path
from run import HERE,LIT,analyze,tail,repair
sys.path.insert(0,str(LIT/'tail-search-v1'))
metrics=tail.module('slot_metrics',LIT/'tail-search-v1/report.py')


def checks(a,b,ids,readiness=False):
    v,w=a['validation'],b['validation'];pair=metrics.paired(a['per_problem'],b['per_problem'],ids)
    full=v['covered']==w['covered']==len(ids)
    result={'fit_coverage':a['fit']['covered']==300,'validation_coverage':full,
            'source_qualification':all(r['qualified_source'] for r in a['per_problem'].values()),
            'audits_clean':not a['illegal_entry_sha256'],'worsened_at_most_25':pair['worse']<=25}
    result.update(actions_5_percent=full and v['actions']['total']<=.95*w['actions']['total']) if readiness else result.update(actions_lower=full and v['actions']['total']<w['actions']['total'])
    for key in ('median','p90'):
        result[key+('_lower' if readiness else '_nonincrease')]=full and (v['actions'][key]<w['actions'][key] if readiness else v['actions'][key]<=w['actions'][key])
    result['fallback_nonincrease']=full and v['single_character_fraction']<=w['single_character_fraction']
    result['package_within_105_percent']=full and v['package_bytes']<=1.05*w['package_bytes']
    if readiness:result['improved_60']=pair['better']>=60
    return result


def main(folder,work):
    raw=(folder/'results.json').read_bytes();r=json.loads(raw);c=json.loads((HERE/'contract.json').read_text())
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes())
    root=work/c['seed_relative_path'];sources=json.loads((root/'sources.json').read_text())
    for rel,h in c['private_files'].items():assert analyze.sha((work/rel).read_bytes())==h
    fit={str(i):sources[str(i)] for i in c['partition']['dev_fit']};observed=set(''.join(fit.values()));reserved=set(repair.ALPHABET)-observed
    old=json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text());old={a['arm']:a for a in old['arms'] if a['width']==8}
    proof=json.loads((LIT/'lns-naming-v1/evidence/results.json').read_text());proof=next(a for a in proof['arms'] if a['arm']=='seed_fixed_seed')
    assert analyze.sha((LIT/'lns-naming-v1/evidence/results.json').read_bytes())==c['qualification_evidence_sha256']
    assert json.loads((folder/'all-fit-sealed.json').read_text())['validation_loaded'] is False
    arms={a['arm']:a for a in r['arms']};ids=c['partition']['dev_val'];assert set(arms)=={'seed','fixed96','optional'}
    for name,a in arms.items():
        d=folder/name;vocab=json.loads((d/'dictionary.json').read_text());db=(d/'dictionary.bin').read_bytes()
        assert analyze.sha((d/'dictionary.json').read_bytes())==a['dictionary_sha256'] and db==analyze.dictionary_bytes(vocab)
        assert set(a['per_problem'])==set(sources) and reserved<=set(vocab) and len(set(vocab))==len(vocab)<=256
        a.update(reserved_unseen_character_entries=len(reserved),observed_character_entries=sum(len(s)==1 and s in observed for s in vocab),dictionary_binary_sha256=analyze.sha(db))
        if a['search']:
            seal=json.loads((d/'fit-seal.json').read_text());assert not seal['validation_loaded']
            assert seal['dictionary_sha256']==a['dictionary_sha256'] and seal['fit_source_sha256']==c['private_files'][c['seed_relative_path']+'/fit-sources.json']
            assert analyze.sha((d/'fit-seal.json').read_bytes())==a['search']['fit_seal_sha256']
            assert analyze.sha((d/'pool.json').read_bytes())==seal['pool_sha256']==a['search']['pool_sha256']
            previous=a['search']['initial_fit_selections']
            for move in a['search']['moves']:
                assert not move['validation_loaded'] and move['before']==previous
                if move['accepted']:
                    file=d/f'incumbent-{move["move"]:02d}.json';assert analyze.sha(file.read_bytes())==move['dictionary_sha256']
                    vd=json.loads(file.read_text());score,_,_=repair.exact(fit,vd)
                    assert score==move['exact']==move['incumbent'] and score<previous and reserved<=set(vd)
                previous=move['incumbent']
            assert previous==a['fit']['selections']['total']==a['search']['fit_selections']
        for pid,row in a['per_problem'].items():
            text=sources[pid];assert row['source_sha256']==analyze.sha(text.encode())==proof['per_problem'][pid]['source_sha256']
            assert row['qualified_source'] and proof['qualification'][pid]['passed']
            try:seq=analyze.shortest_encode(text,vocab)
            except ValueError:assert not row['encodable'];continue
            assert row['encodable'];packet=(d/'packets'/f'{pid}.bin').read_bytes()
            assert analyze.decode(db,packet)==text and packet==analyze.encode(vocab,seq,8)
            assert analyze.sha(packet)==row['packet_sha256'] and row['selections']==len(seq)==len(packet)-41
            assert row['single_characters']==sum(len(vocab[i])==1 for i in seq)
            row.update(one_program_package_bytes=len(db)+len(packet),one_program_with_decoder=len(db)+len(packet)+c['decoder_dependency_bytes'])
        for split,key in [('fit','dev_fit'),('validation','dev_val')]:
            rec=tail.aggregate(a['per_problem'],c['partition'][key],len(db))
            for field in ('covered','failed_ids','actions','selections','single_character_fraction','package_bytes'):assert rec[field]==a[split][field]
            a[split].update(dictionary_bytes=len(db),full_cohort_cost_available=rec['covered']==rec['problems'],
                amortized_package_per_encoded_program=rec['package_bytes']/rec['covered'] if rec['covered'] else None)
    for name,a in arms.items():
        bases={'R':old['control'],'seed':arms['seed'],'fixed96':arms['fixed96']}
        a['paired']={k:metrics.paired(a['per_problem'],b['per_problem'],ids) for k,b in bases.items()}
        a['readiness_checks']=checks(a,old['control'],ids,True);a['ready']=all(a['readiness_checks'].values())
        a['incremental_checks']={k:checks(a,b,ids) for k,b in bases.items() if k!='R'}
        a['successor']=name=='optional' and a['ready'] and all(all(q.values()) for q in a['incremental_checks'].values())
        a['m1_cost_indicators_only']=metrics.indicators(a)
    opt=arms['optional'];control=arms['fixed96'];seed=arms['seed']
    r['predictions']={'A1':all(seed[s]['selections']['total']==old['scope_joint'][s]['selections']['total'] for s in ('fit','validation')) and all(a['fit']['covered']==300 and a['fit']['selections']['total']<=seed['fit']['selections']['total'] for a in arms.values()),
        'A2':opt['character_entries']<96,'A3':opt['fit']['selections']['total']<control['fit']['selections']['total'],
        'A4':opt['validation']['covered']==100,'A5':opt['validation']['covered']==control['validation']['covered']==100 and opt['validation']['actions']['total']<control['validation']['actions']['total'],
        'A6':not opt['successor']}
    r.update(selected_successor='optional' if opt['successor'] else None,private_results_sha256=analyze.sha(raw),decoder_dependency_bytes=c['decoder_dependency_bytes'],offline_encoder_bytes=c['offline_encoder_bytes'],offline_encoder_scope=c['offline_encoder_scope'])
    def clean(x):
        if isinstance(x,dict):
            assert not {'sources','vocab','tokens','trace','_trace','cases','args','failures'}&set(x)
            for value in x.values():clean(value)
        elif isinstance(x,list):
            for value in x:clean(value)
    clean(r);(HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Coverage-constrained character-slot selection','','[Freeze](FREEZE.md); [review/run receipt](REVIEW.md); [metadata evidence](evidence/results.json). Private sources, dictionaries and packets remain private.','',
        f'Selected successor: **{r["selected_successor"] or "none"}**. Optional retains {opt["character_entries"]} character entries and covers {opt["validation"]["covered"]}/100 validation programs. Adaptive consumed-development evidence; no M1 qualification or independent confirmation.','',
        '| Arm | Split | Encoded / source-qualified | Selections | Median/p90/p95/worst | <=32/96 | Actions | Character codes/fraction | Raw package | With decoder sources |','| --- | --- | --- | ---: | --- | --- | ---: | --- | ---: | ---: |']
    for name,a in arms.items():
        for split in ('fit','validation'):
            d=a[split];s=d['selections'];act=d['actions'];frac=d['single_character_fraction'];scope='' if d['full_cohort_cost_available'] else ' (PARTIAL)'
            lines.append(f'| {name} | {split}{scope} | {d["covered"]}/{d["qualified"]} | {s["total"] if s else "NA"} | {"/".join(str(s[k]) for k in ("median","p90","p95","worst")) if s else "NA"} | {str(s["within_32"])+"/"+str(s["within_96"]) if s else "NA"} | {act["total"] if act else "NA"} | {d["single_character_codes"]}/{format(100*frac,".2f")+"%" if frac is not None else "NA"} | {d["package_bytes"]} | {d["package_with_decoder_dependencies"]} |')
    lines+=['','Qualification is reused by exact source hash from item15 seed_fixed_seed, not new execution. Every encoded packet is independently decoded. Partial totals exclude unencodable rows and are not complete-cohort gains; failures remain regressions. One Finish, eight-bit selections, complete dictionary and 41-byte frames are charged; per-program and amortized costs are in evidence.','',
        '| Arm | Comparator | Full-cohort action delta | Better/same/worse | Failed checks |','| --- | --- | ---: | --- | --- |']
    fail=lambda d:', '.join(k for k,v in d.items() if not v) or 'None'
    for name,a in arms.items():
        for base,pair in a['paired'].items():
            b=old['control'] if base=='R' else arms[base];v,w=a['validation'],b['validation'];delta=v['actions']['total']-w['actions']['total'] if v['covered']==w['covered']==100 else 'Unavailable'
            lines.append(f'| {name} | {base} | {delta} | {pair["better"]}/{pair["same"]}/{pair["worse"]} | {fail(a["readiness_checks"] if base=="R" else a["incremental_checks"][base])} |')
    lines+=['','| Arm | Character / learned entries | Reserved unseen / observed chars | Fit start/end | Accepted/attempted | Stop/seconds |','| --- | --- | --- | --- | --- | --- |']
    for name,a in arms.items():
        s=a['search'];lines.append(f'| {name} | {a["character_entries"]}/{a["learned_entries"]} | {a["reserved_unseen_character_entries"]}/{a["observed_character_entries"]} | {str(s["initial_fit_selections"])+"/"+str(s["fit_selections"]) if s else "Pinned"} | {str(sum(m["accepted"] for m in s["moves"]))+"/"+str(len(s["moves"])) if s else "0/0"} | {s["stop"]+"/"+format(s["seconds"],".2f") if s else "Pinned"} |')
    lines+=['','The optional arm frees observed characters only; all fit-unseen characters remain reserved. Exact selected-entry flow has no free character arcs. Both arms use the same bounded repair budget and fixed sources, with no polish or validation repair. Status0 concerns only a restricted candidate repair; time-limited feasible results are not optimality certificates.','',
        '| Prediction | Met |','| --- | --- |']+[f'| {k} | {v} |' for k,v in r['predictions'].items()]
    lines+=['',f'{r["decoded_packets"]} final packets decoded; run wall time {r["seconds"]:.2f} seconds. Four synthetic tests include40exhaustive mixed-entry MILPs; compile/import/help and pinned identity checks passed. Reporting replays all accepted dictionaries and final packets without refitting.','',
        'Item23 retains its unchanged-source1079 exit137 failure. Item15 was independently frozen and launched before that outcome; reusing its passing receipt here does not revise or retry item23. Finite development qualification is not universal equivalence.','',
        'Component intent preserved; canonical codec and production boundaries unchanged. No hidden escape or missing coverage repair. Decoder source inventory is charged separately; complete installed runtime footprint remains unmeasured. Protected opening, confirmation, deployment, training, publication and human studies remain owner-gated.','',
        'Rebuild: `python3 -B projects/algorithm_solver/literals/character-slots-v1/report.py --run /private/character-slots/run-v1 --work /private/literal-admission500-v1`.','']
    (HERE/'README.md').write_text('\n'.join(lines))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);a=ap.parse_args();main(a.run,a.work)
