"""Sanitized local-syntax evidence; replay sealed choices and independent packets."""
import argparse
from collections import Counter
import json
import re
from pathlib import Path
from run import HERE,LIT,analyze,tail
p=tail.module('syntax_metrics',LIT/'tail-search-v1/report.py')


def main(folder):
    raw=(folder/'results.json').read_bytes();r=json.loads(raw);c=json.loads((HERE/'contract.json').read_text())
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes())
    hist=json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text());old={a['arm']:a for a in hist['arms'] if a['width']==8}
    arms={a['arm']:a for a in r['arms']};ids=c['partition']['dev_val'];expected={str(i) for group in c['partition'].values() for i in group}
    assert set(arms)=={'seed','arithmetic','flow','combined','combined_joint'}
    fixed_db=None
    for name,a in arms.items():
        private=folder/f'{name}-256';seal=json.loads((private/'fit-seal.json').read_text());choice=json.loads((private/'choice-seal.json').read_text())
        assert seal['validation_loaded'] is False and choice['qualification_started'] is False
        assert seal['dictionary_sha256']==choice['dictionary_sha256']==a['dictionary_sha256']==analyze.sha((private/'dictionary.json').read_bytes())
        assert choice['sources_sha256']==analyze.sha((private/'sources.json').read_bytes())
        assert seal['fit_sources_sha256']==analyze.sha((private/'fit-sources.json').read_bytes())
        sources=json.loads((private/'sources.json').read_text());fit=json.loads((private/'fit-sources.json').read_text());vocab=json.loads((private/'dictionary.json').read_text())
        assert set(sources)==set(a['per_problem'])==set(a['qualification'])==expected
        assert {str(i):sources[str(i)] for i in c['partition']['dev_fit']}==fit
        db=(private/'dictionary.bin').read_bytes();assert db==analyze.dictionary_bytes(vocab)
        if name=='seed':fixed_db=db
        if name!='combined_joint':assert db==fixed_db
        for pid,row in a['per_problem'].items():
            text=sources[pid];packet=(private/'packets'/f'{pid}.bin').read_bytes()
            assert analyze.decode(db,packet)==text and row['source_sha256']==analyze.sha(text.encode())
            assert row['original_sha256']==old['control']['per_problem'][pid]['source_sha256']
            seq=analyze.shortest_encode(text,vocab);assert packet==analyze.encode(vocab,seq,8) and len(seq)==row['selections']
            assert sum(len(vocab[i])==1 for i in seq)==row['single_characters']
            row.update(source_bytes=len(text.encode()),packet_sha256=analyze.sha(packet),one_program_package_bytes=len(db)+len(packet),
                       one_program_with_decoder=len(db)+len(packet)+c['decoder_dependency_bytes'])
        a['fit_seal_sha256']=analyze.sha((private/'fit-seal.json').read_bytes());a['choice_seal_sha256']=analyze.sha((private/'choice-seal.json').read_bytes())
        for split,split_ids in [('fit',c['partition']['dev_fit']),('validation',ids)]:
            d=a[split];rows=[a['per_problem'][str(i)] for i in split_ids]
            d.update(source_bytes=sum(x['source_bytes'] for x in rows),single_character_codes=sum(x['single_characters'] for x in rows),
                     qualified=sum(a['qualification'][str(i)]['passed'] for i in split_ids),
                     changed_from_R=sum(x['source_sha256']!=x['original_sha256'] for x in rows),
                     changed_from_seed=sum(a['per_problem'][str(i)]['source_sha256']!=old['scope_joint']['per_problem'][str(i)]['source_sha256'] for i in split_ids),
                     package_with_decoder_dependencies=d['package_bytes']+c['decoder_dependency_bytes'],framing_bytes=41*len(rows),
                     payload_bits=8*sum(x['selections'] for x in rows),padding_bits=0)
            d['qualification_failed_ids']=[i for i in split_ids if not a['qualification'][str(i)]['passed']]
    for name,a in arms.items():
        bases={'R':old['control'],'seed':arms['seed'],'arithmetic':arms['arithmetic'],'flow':arms['flow'],'combined':arms['combined']}
        a['paired']={k:p.paired(a['per_problem'],b['per_problem'],ids) for k,b in bases.items()}
        v,b,s=a['validation'],old['control']['validation'],arms['seed']['validation'];pair=a['paired']['R']
        a['readiness_checks']={'qualified':all(q['passed'] for q in a['qualification'].values()),'coverage':v['covered']==100,
            'audits_clean':not a['illegal_entry_sha256'],'actions_5_percent':v['actions']['total']<=.95*b['actions']['total'],
            'median_lower':v['actions']['median']<b['actions']['median'],'p90_lower':v['actions']['p90']<b['actions']['p90'],
            'improved_60':pair['better']>=60,'worsened_at_most_25':pair['worse']<=25,
            'fallback_nonincrease':v['single_character_fraction']<=b['single_character_fraction'],
            'package_within_105_percent':v['package_bytes']<=1.05*b['package_bytes']}
        a['ready']=all(a['readiness_checks'].values())
        a['successor_checks']={'ready':a['ready'],'actions_lower':v['actions']['total']<s['actions']['total'],
            'median_nonincrease':v['actions']['median']<=s['actions']['median'],'p90_nonincrease':v['actions']['p90']<=s['actions']['p90'],
            'fallback_nonincrease':v['single_character_fraction']<=s['single_character_fraction'],
            'package_within_105_percent':v['package_bytes']<=1.05*s['package_bytes'],'worsened_at_most_25':a['paired']['seed']['worse']<=25}
        a['successor']=all(a['successor_checks'].values());a['m1_cost_indicators_only']=p.indicators(a)
    total=lambda n:arms[n]['validation']['actions']['total']
    r['predictions']={'S1':all(arms['seed'][s]['selections']['total']==old['scope_joint'][s]['selections']['total'] for s in ('fit','validation')),
        'S2':arms['arithmetic']['paired']['seed']['better']>=20,'S3':total('combined')<min(total('arithmetic'),total('flow')),
        'S4':total('combined_joint')<=.99*total('seed'),'S5':all(a['qualified']==400 and a['fit']['covered']+a['validation']['covered']==400 and not a['illegal_entry_sha256'] for a in arms.values()),
        'S6':any(a['successor'] for a in arms.values())}
    winners=sorted((a for a in arms.values() if a['successor']),key=lambda a:(a['validation']['actions']['total'],a['validation']['package_bytes'],a['arm']))
    r['selected_successor']=winners[0]['arm'] if winners else None;r['private_results_sha256']=analyze.sha(raw)
    r['decoder_dependency_bytes']=c['decoder_dependency_bytes'];r['offline_encoder_bytes']=c['offline_encoder_bytes'];r['offline_encoder_scope']=c['offline_encoder_scope']
    qs=json.loads((folder/'qualification-private.json').read_text());r['qualification_receipt_sha256']=analyze.sha((folder/'qualification-private.json').read_bytes())
    r['fresh_qualification_summary']={'distinct_sources':len(qs),'passed':sum(q['passed'] for q in qs.values()),'checks_passed':sum(q['checks_passed'] for q in qs.values()),'checks_total':sum(q['cases'] for q in qs.values())}
    new_keys={f'{pid}:{row["source_sha256"]}' for a in arms.values() for pid,row in a['per_problem'].items() if row['source_sha256'] not in (old['scope_joint']['per_problem'][pid]['source_sha256'],old['control']['per_problem'][pid]['source_sha256'])}
    r['new_syntax_source_qualification']={'distinct_sources':len(new_keys),'passed':sum(qs[k]['passed'] for k in new_keys),'checks_passed':sum(qs[k]['checks_passed'] for k in new_keys),'checks_total':sum(qs[k]['cases'] for k in new_keys)}
    r['qualification_failure_metadata']=[]
    for key,q in qs.items():
        if q['passed']:continue
        pid,digest=key.split(':');events=[]
        for event in q['failures']:
            match=re.search(r'sandbox failure \(exit (-?\d+), timed out (True|False)\)',str(event.get('error','')))
            events.append({'batch_offset':event.get('offset'),'kind':'sandbox_exit' if match else 'case_or_protocol_failure',
                           'exit_code':int(match[1]) if match else None,'wall_timed_out':match[2]=='True' if match else None})
        r['qualification_failure_metadata'].append({'id':int(pid),'source_sha256':digest,'checks_passed':q['checks_passed'],'checks_total':q['cases'],
            'same_as_item13_seed':digest==old['scope_joint']['per_problem'][pid]['source_sha256'],
            'item13_qualification_passed':old['scope_joint']['qualification'][pid]['passed'],'events':events})
    def clean(v):
        if isinstance(v,dict):
            assert not {'_trace','trace','accepted_colors','sources','vocab','tokens','failures','replacement','text','changes','name','target'}&set(v)
            for x in v.values():clean(x)
        elif isinstance(v,list):
            for x in v:clean(x)
    clean(r);(HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Vocabulary-aware local syntax alternatives','','[Freeze](FREEZE.md) pushed as `eedae46a2`; [review/run receipt](REVIEW.md); [evidence](evidence/results.json). Source, dictionary, packets and traces remain private.','',
        f'Selected incremental successor: **{r["selected_successor"] or "none"}**. This is adaptive consumed-development evidence, not independent confirmation, autonomous assembly or M1 qualification.','',
        'All validation costs are unchanged at8504actions. Flow and combined save three fit selections; arithmetic saves none, and joint dictionary continuation adds no gain. No incremental successor is selected.','',
        'Fresh qualification passes399/400 in every arm. The same unchanged item13 seed source (#1079) fails one16-case batch with sandbox exit137 and wall_timed_out=false (58/74checks pass). Its earlier item13 receipt passed. This run retains the failure with no retry; the precise kill cause is unestablished. No new syntax change is implicated by the identical failed source hash. Historical item13 results remain unchanged. Both newly selected syntax variants pass their171checks; that does not erase the shared seed failure.','',
        'The fixed arithmetic, flow and combined arms share the seed dictionary. Their exact per-node choices preserve names and algorithms; combined_joint additionally refits the dictionary. Proposal families and trajectories differ under common caps. OriginalR and all prior source variants remain available. Validation runs the same frozen source policy under each fit-sealed dictionary, with no refit or test feedback.','',
        '| Arm | Split | Decoded/qualified | Selections | Median/p90/p95/worst | <=32/96 | Actions | Character codes/fraction | Raw package | With decoder sources |',
        '| --- | --- | --- | ---: | --- | --- | ---: | --- | ---: | ---: |']
    for name,a in arms.items():
        for split in ('fit','validation'):
            d=a[split];s=d['selections'];lines.append(f'| {name} | {split} | {d["covered"]}/{d["qualified"]} | {s["total"]} | {s["median"]}/{s["p90"]}/{s["p95"]}/{s["worst"]} | {s["within_32"]}/{s["within_96"]} | {d["actions"]["total"]} | {d["single_character_codes"]}/{100*d["single_character_fraction"]:.2f}% | {d["package_bytes"]} | {d["package_with_decoder_dependencies"]} |')
    lines+=['','One Finish, complete dictionary, eight-bit payload and41-byte frame charged. Every parenthesis/operator added by a rewrite is literal source and counted. Decoder-source storage is separate; full runtime installation size is unmeasured. Failed choices remain in denominators.','',
        '| Arm | Actions vs seed | Better/same/worse vs seed | Ready vs R | Successor | Failed readiness | Failed successor |','| --- | ---: | --- | --- | --- | --- | --- |']
    fail=lambda d:', '.join(k for k,v in d.items() if not v) or 'None'
    for name,a in arms.items():
        pair=a['paired']['seed'];lines.append(f'| {name} | {total(name)-total("seed")} | {pair["better"]}/{pair["same"]}/{pair["worse"]} | {a["ready"]} | {a["successor"]} | {fail(a["readiness_checks"])} | {fail(a["successor_checks"])} |')
    lines+=['','| Contrast | Validation action delta | Better/same/worse |','| --- | ---: | --- |']
    for n,b in [('combined','arithmetic'),('combined','flow'),('combined_joint','combined')]:
        pair=arms[n]['paired'][b];lines.append(f'| {n} minus {b} | {total(n)-total(b)} | {pair["better"]}/{pair["same"]}/{pair["worse"]} |')
    lines+=['','| Arm | Phase | Trials | Moves | Proposal caps | Unsupported calls | Accepted kinds |','| --- | --- | ---: | ---: | ---: | ---: | --- |']
    for name,a in arms.items():
        if name=='seed':continue
        groups=[(f'fit round{h["round"]+1}',h['rewrite']) for h in a['rounds']]+[(f'validation call{i+1}',g) for i,g in enumerate(a['validation_rewrite'])]
        for phase,stats in groups:
            vals=list(stats.values());kinds=Counter(x['kind'] for st in vals for x in st['accepted'])
            lines.append(f'| {name} | {phase} | {sum(s["trials"] for s in vals)} | {sum(s["moves"] for s in vals)} | {sum(s["proposal_caps"] for s in vals)} | {sum(s["unsupported"] for s in vals)} | {dict(kinds)} |')
    lines+=['','Counts are calls, not distinct programs. Conservative reflection/function-escape guards exclude some functions; capped/local search is not a source or dictionary optimum. Exact search statistics, stops and source changes are in evidence.','',
        '| Prediction | Met |','| --- | --- |']+[f'| {k} | {v} |' for k,v in r['predictions'].items()]
    q=r['fresh_qualification_summary'];lines+=['',f'Distinct final changed sources: {q["passed"]}/{q["distinct_sources"]} qualified, {q["checks_passed"]}/{q["checks_total"]} strict original-case/parity checks. All2000choices seal before execution, no retries or repairs; unchangedR reuses its receipt. Finite reused cases do not prove universal JS equivalence. Measured run wall time: {r["seconds"]:.2f} seconds.','',
        'Four focused Python tests and127 synthetic behavior observations passed before launch, plus parse/compile/import/help. Source observation can matter in JavaScript; guarded unsupported forms are retained, not silently reinterpreted. Component intent and canonical/production behavior preserved.','',
        'Dated context (2026-10-23): [roles-v1’s disclosed rerun](../roles-v1/FREEZE.md) also records an exit137 kill for problem1079 under24workers, followed by a serial pass and a successful four-worker audit. That earlier observation supports investigating resource sensitivity; it does not identify this run’s kill cause or authorize a retry under this freeze.','',
        'Any selected successor requires separately frozen owner-approved confirmation. Private candidate: syntax-choice/run-v1/<selected>-256. No protected opening, training, publication, deployment, human study or ledger/catalog/claim write.','',
        'Rebuild: `python3 -B projects/algorithm_solver/literals/syntax-choice-v1/report.py --run /private/syntax-choice/run-v1`.','']
    (HERE/'README.md').write_text('\n'.join(lines))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);main(ap.parse_args().run)
