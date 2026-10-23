"""Sanitized template cost, eligibility, usage and explicit byte-sharing attribution."""
import argparse
from collections import Counter
import json
from pathlib import Path
from run import HERE,LIT,analyze,codec


def paired(a,b,ids):
    ds=[a[str(i)]['actions']-b[str(i)]['actions'] for i in ids]
    return {'n':len(ids),'better':sum(d<0 for d in ds),'same':sum(d==0 for d in ds),'worse':sum(d>0 for d in ds),
            'action_delta':sum(ds),'typed_actions':sum(a[str(i)]['actions'] for i in ids),'literal_actions':sum(b[str(i)]['actions'] for i in ids)}


def main(folder):
    raw=(folder/'results.json').read_bytes();r=json.loads(raw);c=json.loads((HERE/'contract.json').read_text());ids=c['partition']['dev_val']
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes())
    hist=json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text());historical={a['arm']:a for a in hist['arms'] if a['width']==8}
    expected={str(i) for group in c['partition'].values() for i in group};arms={(a['cohort'],a['arm']):a for a in r['arms']}
    assert set(arms)=={(co,n) for co in ('R','naming') for n in ('literal','typed')}
    for (co,n),a in arms.items():
        private=folder/f'{co}-{n}-256';seal=json.loads((private/'fit-seal.json').read_text());texts=json.loads((private/'sources.json').read_text())
        assert seal['validation_loaded'] is False and seal['dictionary_sha256']==a['dictionary_sha256']==analyze.sha((private/'dictionary.bin').read_bytes())
        assert seal['dictionary_json_sha256']==analyze.sha((private/'dictionary.json').read_bytes())
        assert seal['pool_sha256']==analyze.sha((private/'pool.json').read_bytes());a['pool_sha256']=seal['pool_sha256']
        assert set(a['per_problem'])==set(texts)==expected
        keys=json.loads((private/'dictionary.json').read_text());usage=[Counter() for _ in keys];plans={}
        previous=historical['control' if co=='R' else 'scope_joint']
        for pid,row in a['per_problem'].items():
            assert row['source_sha256']==previous['per_problem'][pid]['source_sha256']==analyze.sha(texts[pid].encode()) and previous['qualification'][pid]['passed']
            pkt=(private/'packets'/f'{pid}.bin').read_bytes();assert analyze.sha(pkt)==row['packet_sha256'];codes=list(pkt[41:])
            assert len(codes)==row['selections'];tokens=[keys[i] for i in codes];plans[pid]={'tokens':tokens}
            if n=='typed':assert codec.packet(keys,tokens,8)==pkt
            else:assert analyze.decode((private/'dictionary.bin').read_bytes(),pkt)==texts[pid]
            split='fit' if int(pid) in c['partition']['dev_fit'] else 'validation'
            for code,count in Counter(codes).items():usage[code][split+'_programs']+=1;usage[code][split+'_codes']+=count
            row['one_program_package_bytes']=a['dictionary_bytes']+row['packet_bytes'];row['one_program_with_decoder']=row['one_program_package_bytes']+a['decoder_dependency_bytes']
        if n=='typed':assert codec.decode_many(keys,plans,8)==texts
        a['entry_metadata']=[{'key_sha256':analyze.sha(key.encode()),'kind':key[0],
            'literal_bytes':len(key[1:].encode()) if key[0]=='L' else None,
            'constructor_spec_bytes':len(key[1:].encode()) if key[0]=='C' else None,**dict(u)} for key,u in zip(keys,usage)]
        a['fit_seal_sha256']=analyze.sha((private/'fit-seal.json').read_bytes())
        v=a['validation'];a['m1_cost_indicators_only']=v['covered']==100 and not a['illegal_entry_sha256'] and v['selections']['median']<=32 and v['selections']['p95']<=96 and v['single_character_fraction']<=.1
    for co in ('R','naming'):
        a,b=arms[co,'typed'],arms[co,'literal'];assert a['validation_eligible_ids']==b['validation_eligible_ids'] and a['pool_sha256']==b['pool_sha256']
        eligible=a['validation_eligible_ids'];used=[i for i in ids if a['per_problem'][str(i)]['constructor_codes']]
        a['paired']={name:paired(a['per_problem'],b['per_problem'],part) for name,part in [('all',ids),('eligible',eligible),('complement',[i for i in ids if i not in eligible]),('used',used),('unused',[i for i in ids if i not in used])]}
        v,bv=a['validation'],b['validation'];p=a['paired']['all']
        a['readiness_checks']={'coverage_qualification':v['covered']==v['qualified']==100,'audits_clean':not a['illegal_entry_sha256'],
            'actions_5_percent':v['actions']['total']<=.95*bv['actions']['total'],'median_lower':v['actions']['median']<bv['actions']['median'],
            'p90_lower':v['actions']['p90']<bv['actions']['p90'],'improved_60':p['better']>=60,'worsened_at_most_25':p['worse']<=25,
            'fallback_nonincrease':v['single_character_fraction']<=bv['single_character_fraction'],'package_within_105_percent':v['package_bytes']<=1.05*bv['package_bytes']}
        a['ready']=all(a['readiness_checks'].values())
    gain=lambda co:1-arms[co,'typed']['validation']['actions']['total']/arms[co,'literal']['validation']['actions']['total']
    r['predictions']={
        'I1':all(a['initial_fit_selections']==historical['control' if co=='R' else 'scope_joint']['fit']['selections']['total'] and a['initial_validation_selections']==historical['control' if co=='R' else 'scope_joint']['validation']['selections']['total'] for (co,n),a in arms.items()),
        'I2':arms['R','typed']['validation']['constructor_programs']>=20,
        'I3':all(gain(co)>=.05 for co in ('R','naming')),'I4':gain('R')>gain('naming'),
        'I5':all(a['fit']['covered']+a['validation']['covered']==400 and a['fit']['qualified']+a['validation']['qualified']==400 and not a['illegal_entry_sha256'] for a in arms.values()),
        'I6':not any(a['m1_cost_indicators_only'] for a in arms.values())}
    ready=sorted((a for a in arms.values() if a.get('ready')),key=lambda a:(a['validation']['actions']['total'],a['validation']['package_bytes'],a['cohort']))
    r['selected_structured_candidate']=ready[0]['cohort'] if ready else None;r['private_results_sha256']=analyze.sha(raw);r['offline_tooling_bytes']=c['offline_tooling_bytes']
    def clean(v):
        if isinstance(v,dict):
            assert not {'keys','tokens','trace','sources','constructors','expression_literals','parts','spec','dictionary','args','uses'}&set(v)
            for x in v.values():clean(x)
        elif isinstance(v,list):
            for x in v:clean(x)
    clean(r);(HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Mined identifier templates','','[Freeze](FREEZE.md) pushed as `d6a27667e`; [review/run receipt](REVIEW.md); [evidence](evidence/results.json). All source, template specifications, dictionaries, packets and traces remain private.','',
        f'Selected structured input candidate: **{r["selected_structured_candidate"] or "none"}**. This is separate goal2c, with fixed qualified source bytes. Consumed-development readiness does not qualify flat-literal M1, autonomous assembly or independent generalization.','',
        'Each constructor and each distinct identifier argument consumes a code; repeats are defined by charged dictionary metadata. An unavailable complete identifier literal disables that template match. Independent decoding checks every insertion is an exact Identifier span/name, expansion root shape, and per-use whole-solution exclusion. No semantic binding or source rewrite occurs.','',
        '| Cohort | Arm | Split | Selections | Median/p90/p95/worst | <=32/96 | Actions | Character codes/fraction | Template codes/programs | Raw package | With decoder sources |',
        '| --- | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | ---: |']
    for (co,n),a in arms.items():
        for split in ('fit','validation'):
            d=a[split];s=d['selections']
            lines.append(f'| {co} | {n} | {split} | {s["total"]} | {s["median"]}/{s["p90"]}/{s["p95"]}/{s["worst"]} | {s["within_32"]}/{s["within_96"]} | {d["actions"]["total"]} | {d["single_character_codes"]}/{100*d["single_character_fraction"]:.2f}% | {d["constructor_codes"]}/{d["constructor_programs"]} | {d["package_bytes"]} | {d["package_with_decoder_dependencies"]} |')
    lines+=['','Every arm covers/decodes/qualifies300fit and100validation programs; qualification is exact-source hash reuse, not new case execution. One Finish each; complete metadata,41-byte framing and eight-bit payload charged. Typed decoder+Acorn and literal decoder source dependencies are separate from raw packages. Full language/runtime installations remain unmeasured.','',
        '| Cohort | Arm | Split | Argument codes | Fixed template bytes | Repeated identifier bytes | Total free-byte share | Maximum program share |','| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for (co,n),a in arms.items():
        for split in ('fit','validation'):
            d=a[split];lines.append(f'| {co} | {n} | {split} | {d["argument_codes"]} | {d["fixed_template_bytes"]} | {d["repeated_identifier_bytes"]} | {100*d["free_byte_fraction"]:.2f}% | {100*d["max_program_free_byte_fraction"]:.2f}% |')
    lines+=['','“Free bytes” means fixed/copied source bytes generated by a charged template/argument selection. The template metadata is stored and charged; this is compression, not an external payload. Each use is below half a program and cannot equal the solve/body. Aggregate share is reported rather than constrained by a new global cap.','',
        '| Cohort | Subset | Programs | Typed/literal actions | Delta | Better/same/worse |','| --- | --- | ---: | --- | ---: | --- |']
    for co in ('R','naming'):
        for name,p in arms[co,'typed']['paired'].items():lines.append(f'| {co} | {name} | {p["n"]} | {p["typed_actions"]}/{p["literal_actions"]} | {p["action_delta"]} | {p["better"]}/{p["same"]}/{p["worse"]} |')
    lines+=['','Eligibility is a match from the sealed fit template pool, before dictionary choice. Used/unused subsets are outcome-dependent descriptive attribution. All are typed minus matched searched literal. Pool hashes match between paired arms; their selected-span proposals can diverge after encoding changes.','',
        '| Cohort | Arm | Template entries | Template/literal pool | Trials | Rounds | Stop | Search seconds |','| --- | --- | ---: | --- | ---: | ---: | --- | ---: |']
    for (co,n),a in arms.items():
        s=a['search'];lines.append(f'| {co} | {n} | {a["constructor_entries"]} | {a["constructor_pool_count"]}/{a["expression_literal_pool_count"]} | {s["trials"]} | {s["rounds"]} | {s["stop"]} | {s["seconds"]:.2f} |')
    for co in ('R','naming'):
        a=arms[co,'typed'];failed=', '.join(k for k,v in a['readiness_checks'].items() if not v) or 'None'
        lines += ['',f'{co}: {100*gain(co):.2f}% fewer validation actions, ready={a["ready"]}; failed predicates: {failed}.']
    lines+=['','Local/time/trial stops describe a bounded neighborhood, not grammar or global dictionary optimality. Every failed predicate and conditional result remains visible.','',
        '| Prediction | Met |','| --- | --- |']+[f'| {k} | {v} |' for k,v in r['predictions'].items()]
    lines += ['',f'Measured run wall time: {r["seconds"]:.2f} seconds. Twelve focused synthetic tests plus compilation/import/help passed before launch. All1600packets independently decode and are replayed during reporting; source/packet/pool/fit-seal hashes, entry size/reuse and full cost distributions are in evidence.', '',
        'Owner gate: any structured candidate needs a separately frozen owner-approved confirmation population and exact codebook/encoder. Candidate artifacts: identifier-templates/run-v1/<cohort>-typed-256. No protected/held-out opening, model training, source publication, BITS deployment, human study, ledger/catalog/claim write or M1 threshold change. Component intent preserved; this decoder is isolated from canonical literals and production.', '',
        'Rebuild: `python3 -B projects/algorithm_solver/literals/identifier-templates-v1/report.py --run /private/identifier-templates/run-v1`.','']
    (HERE/'README.md').write_text('\n'.join(lines))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);main(ap.parse_args().run)
