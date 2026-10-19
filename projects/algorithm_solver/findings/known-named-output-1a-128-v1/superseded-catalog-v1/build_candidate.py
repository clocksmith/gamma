"""Chain nine fresh candidate verdicts to complete current evidence; verify opt-in serving."""
import argparse
import json
from pathlib import Path
import time
from algsolve import library_audit as audit
from algsolve.approved_library import ApprovedLibrary,build,code_hash,digest
from algsolve.catalog_refresh import query_for,_validate_rows
from algsolve.named_lookup import adapter_record,load_context,answer
from algsolve.qualification_environment import capture,verify
from algsolve.records import LANE_ROOT

REPORT=Path(__file__).parent
BASE=LANE_ROOT/'runs/catalog-refresh-128-v4'
NINE=LANE_ROOT/'runs/known-named-output-1a-128-v2'
OUT=LANE_ROOT/'runs/known-named-catalog-128-v1'


def build_candidate():
    original=ApprovedLibrary.load(BASE/'approved-library.json');original.verify_runtime(LANE_ROOT)
    base_contract=json.loads((BASE/'contract.json').read_text());nine_contract=json.loads((NINE/'contract.json').read_text())
    for contract in [base_contract,nine_contract]:
        for relative,sha in contract['files_sha256'].items():assert audit.sha(LANE_ROOT/relative)==sha,relative
    verify(nine_contract['runtime_environment'])
    _,entries,_,boundary=audit.inputs();assert audit.digest(boundary)==base_contract['boundary_sha256']
    rows=audit.rows(BASE/'answers.jsonl');bykey={r['key']:r for r in rows}
    assert _validate_rows(rows,{e.key for e in entries})=={e.key for e in entries}
    seal=json.loads((NINE/'decisions-seal.json').read_text());assert audit.sha(NINE/'decisions.json')==seal['sha256'] and seal['count']==18
    decisions=[r for r in json.loads((NINE/'decisions.json').read_text()) if r['arm']=='candidate']
    stored=json.loads((NINE/'stored-scores.json').read_text());scores=json.loads((NINE/'scores.json').read_text())
    scores={r['key']:r for r in scores if r['arm']=='candidate'}
    replaced=set()
    for row in decisions:
        key=row['key'];assert key not in original.manifest['approved'] and key not in replaced
        result=row['result'];score=scores[key];saved={k:v for k,v in result.items() if k!='code'}
        saved['code_sha256']=code_hash(result['code']) if result.get('code') else None
        identity=(result.get('match') or {}).get('key')==key
        bykey[key]={'key':key,'accepted_and_correct':score['correct'],'stored_solution':stored[key],
            'returned_solution':score['independent'],'result':saved,'identity_correct':identity,
            'accepted':result['decision']=='answered','fresh_execution':True,'evidence_origin':'frozen named-output v2 nine-case comparison'}
        replaced.add(key)
    assert replaced==set(nine_contract['keys']) and len(replaced)==9
    combined=[bykey[r['key']] for r in rows]
    runtime=dict(original.manifest['runtime_files_sha256'])
    for name in ['algsolve/named_output_contracts.py','algsolve/named_lookup.py']:
        runtime[name]=audit.sha(LANE_ROOT/name)
    OUT.mkdir(exist_ok=False)
    with (OUT/'answers.jsonl').open('w') as stream:
        for row in combined:stream.write(json.dumps(row)+'\n')
    (OUT/'inventory.jsonl').write_bytes((BASE/'inventory.jsonl').read_bytes())
    proof={'base_catalog_sha256':audit.sha(BASE/'approved-library.json'),'base_answers_sha256':audit.sha(BASE/'answers.jsonl'),
        'nine_contract_sha256':audit.sha(NINE/'contract.json'),'nine_decisions_seal_sha256':audit.sha(NINE/'decisions-seal.json'),
        'nine_scores_sha256':audit.sha(NINE/'scores.json'),'nine_stored_scores_sha256':audit.sha(NINE/'stored-scores.json'),
        'combined_answers_sha256':audit.sha(OUT/'answers.jsonl'),'replaced_only':sorted(replaced),
        'old_approved_rows_replaced':0,'fresh_v4_rows_reused':len(rows)-9,'new_independent_sets_executed':9,
        'historical_pass_flags_reused':False,'query_adapter':adapter_record(),
        'existing_runtime_source_changes':[],'runtime_environment':capture(),
        'full_serving_verification':'pending; all3288 eligible under explicit wrapper'}
    manifest=build(entries,audit.rows(OUT/'inventory.jsonl'),combined,evidence=proof,runtime_files=runtime,
        answer_policy=original.manifest['answer_policy'],runtime_environment=proof['runtime_environment'])
    body={k:v for k,v in manifest.items() if k!='sha256'};body['query_adapter']=adapter_record()
    manifest=dict(body,sha256=digest(body));assert manifest['counts']['approved']==2487
    assert all(manifest['approved'][k]==value for k,value in original.manifest['approved'].items())
    audit.write(OUT/'approved-library.json',manifest);audit.write(OUT/'rebind-proof.json',proof)
    audit.write(OUT/'verification-contract.json',{'catalog_sha256':audit.sha(OUT/'approved-library.json'),
        'runner_sha256':audit.sha(Path(__file__)),'inventory_sha256':audit.sha(OUT/'inventory.jsonl'),
        'query_builder_sha256':audit.sha(LANE_ROOT/'algsolve/catalog_refresh.py'),
        'problem_records_sha256':audit.sha(LANE_ROOT/'data/derived/problems.jsonl'),
        'boundary_sha256':audit.digest(boundary),'eligible':len(entries),'limits':{'threads':2,'memory_bytes':2*1024**3,'chunk_wall_seconds':240},
        'timing':'contended; no latency claim'})
    print(json.dumps(manifest['counts'],indent=2))


def verify_serving():
    start=time.monotonic();frozen=json.loads((OUT/'verification-contract.json').read_text())
    assert frozen['catalog_sha256']==audit.sha(OUT/'approved-library.json')
    assert frozen['runner_sha256']==audit.sha(Path(__file__))
    assert frozen['query_builder_sha256']==audit.sha(LANE_ROOT/'algsolve/catalog_refresh.py')
    assert frozen['problem_records_sha256']==audit.sha(LANE_ROOT/'data/derived/problems.jsonl')
    context,catalog=load_context(OUT/'approved-library.json');_,entries,problems,boundary=audit.inputs()
    assert frozen['boundary_sha256']==audit.digest(boundary)
    path=OUT/'verified.jsonl';rows=audit.rows(path) if path.exists() else [];done=_validate_rows(rows,{e.key for e in entries})
    for entry in entries:
        if entry.key in done:continue
        if time.monotonic()-start>=240:break
        query,_=query_for(entry,problems);r=answer(context,query,approved_library=catalog)
        approved=entry.key in catalog.manifest['approved'];expected=catalog.manifest['approved'].get(entry.key,{})
        passed=(r['decision']=='answered' and r.get('code') and code_hash(r['code'])==expected['code_sha256'] and
                r.get('example_passed') and (r.get('match') or {}).get('key')==entry.key) if approved else r['decision']=='abstain' and r.get('code') is None
        record={'key':entry.key,'approved':approved,'passed':bool(passed),'decision':r['decision'],'reason':r.get('reason')}
        with path.open('a') as stream:stream.write(json.dumps(record)+'\n');stream.flush()
        rows.append(record);done.add(entry.key)
        if len(done)%200==0:print('[serving]',len(done),'/',len(entries),flush=True)
    catalog.verify_runtime(LANE_ROOT)
    summary={'eligible':len(entries),'verified':len(rows),'complete':len(rows)==len(entries),
        'approved_answered':sum(r['approved'] and r['passed'] for r in rows),
        'excluded_abstained':sum(not r['approved'] and r['passed'] for r in rows),
        'failures':[r for r in rows if not r['passed']],'encoder_loaded':context.embedder.encoder is not None,
        'approved_independent_tests_passed':sum(v['tests_passed'] for r in catalog.manifest['approved'].values() for v in r['independent_verdicts']),
        'existing_catalog_still_valid':True,'runtime_unchanged':True}
    ApprovedLibrary.load(BASE/'approved-library.json').verify_runtime(LANE_ROOT)
    audit.write(OUT/'serving-summary.json',summary)
    if summary['complete']:
        for name in ['approved-library.json','rebind-proof.json','verification-contract.json','serving-summary.json']:(REPORT/name).write_bytes((OUT/name).read_bytes())
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','verify']);a=p.parse_args()
    {'build':build_candidate,'verify':verify_serving}[a.action]()
