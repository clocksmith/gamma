"""Bounded resumable fresh catalog qualification; no old execution flags promoted.

All exact-query public decisions are sealed before independent scoring starts.
Every eligible entry receives an outcome. The old catalog and imported files
remain immutable; missing evidence and incomplete refreshes never approve code.
"""
import argparse
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
import time
import numpy as np
from . import corpus, library_audit as audit
from .answer import answer
from .approved_library import ApprovedLibrary, build, code_hash, entry_hash, selected_reference, load_context
from .imported_examples import repair
from .lookup import LookupIndex, load_thresholds
from .records import DERIVED, LANE_ROOT
from .routes import Budget, Context

POLICY={'public_output_contracts':True}
SERVING=['answer.py','approved_library.py','lookup.py','interface_compatibility.py','embed.py',
         'public_examples.py','public_contracts.py','importers.py','values.py','validate.py',
         'editor_execution.py','editor_task.py','editor_bridge.py','records.py','corpus.py',
         'splits.py','routes.py']


def _rows(path):return audit.rows(path) if path.exists() else []

def _append(path,row):
    with path.open('a') as f:f.write(json.dumps(row,allow_nan=False)+'\n');f.flush()


def query_for(entry,problems):
    primary,_=audit.original_for(entry,problems);receipt={'changed':False}
    if (primary is not None and primary.statement==entry.statement and primary.entry==entry.entry
            and primary.params==entry.params and primary.starter_code==entry.starter_code):
        primary,receipt=repair(primary)
    return audit.exact_query(entry,primary),receipt


def _paths():
    runtime=[LANE_ROOT/'algsolve'/name for name in SERVING]+sorted((LANE_ROOT/'algsolve/judge').glob('*.py'))
    runtime += [corpus.ENTRIES_PATH,corpus.KEYS_PATH,corpus.EMBEDDINGS_PATH]+[
        LANE_ROOT/'contracts'/name for name in ['run_contract.json','lookup_thresholds.json','statement_lookup_thresholds.json']]
    inputs=[DERIVED/'problems.jsonl',DERIVED/'near_duplicates.json',LANE_ROOT/'contracts/typed_confirmation_v1.json',
            LANE_ROOT/'findings/library-answer-audit-v2/inventory.jsonl',LANE_ROOT/'algsolve/imported_examples.py',
            LANE_ROOT/'algsolve/library_audit.py',LANE_ROOT/'algsolve/recognition_boundary.py',Path(__file__)]
    return runtime,inputs


def freeze(directory):
    raw,entries,problems,boundary=audit.inputs();old={r['key']:r for r in audit.rows(LANE_ROOT/'findings/library-answer-audit-v2/inventory.jsonl')}
    eligible={e.key:e for e in entries};inventory=[];test_files={}
    for row in raw:
        if row['key'] not in eligible:
            inventory.append({'key':row['key'],'excluded':'protected_composition_alias'});continue
        e=eligible[row['key']];record=dict(old[e.key]);q,receipt=query_for(e,problems)
        if record.get('excluded'):raise ValueError('Current eligible key was previously protected')
        # Existing inventory supplies test identity/counts only, never pass flags.
        expected_refs={r['code_sha256'] for r in record['references']}
        if any(code_hash(r['code']) not in expected_refs for r in e.references):raise ValueError('Reference inventory drift')
        primary,sources=audit.original_for(e,problems)
        actual={(s.uid,s.hidden_tests_path) for s in sources}
        for tests in record['independent_test_sets']:
            if (tests['uid'],tests['path']) not in actual:raise ValueError('Independent source identity drift')
            path=Path(tests['path']);path=path if path.is_absolute() else DERIVED/path
            # Hash bytes at freeze; decode expected outputs only after decisions seal.
            test_files[str(path.resolve())]=audit.sha(path)
        record.update(identity_valid=e.key=='lc:'+e.slug and bool(e.title and e.members),
                      provenance_present=bool(e.license and e.attribution) and all(
                          r.get('uid') in e.members and r.get('source') and r.get('code') for r in e.references),
                      interface_compatible=primary is not None,
                      public_examples=len(q.public_tests),public_sha256=audit.digest(q.public_tests),
                      entry_sha256=entry_hash(e),input_repair=receipt)
        inventory.append(record)
    runtime,inputs=_paths();allfiles=runtime+inputs
    contract={'schema':'algsolve.catalog-refresh.v2','inventory':len(raw),'eligible':len(entries),
        'protected_present':len(raw)-len(entries),'boundary_sha256':audit.digest(boundary),
        'files_sha256':{str(p.relative_to(LANE_ROOT)):audit.sha(p) for p in allfiles},
        'runtime_files_sha256':{str(p.relative_to(LANE_ROOT)):audit.sha(p) for p in runtime},
        'test_artifact_sha256':test_files,'inventory_sha256':audit.digest(inventory),'answer_policy':POLICY,
        'public_phase':'all eligible exact queries executed with no model/generation; then global decision seal',
        'independent_phase':'fresh all-compatible independent tests for every selected stored reference, including public abstentions',
        'not_reused':'No historical pass verdict or approval authorizes any refreshed entry',
        'limits':{'threads':2,'memory_bytes':2*1024**3,'disk_bytes':1024**3,'maximum_chunk_wall_seconds':300,
                  'judge_wall_seconds':30,'route_wall_seconds':120},'timing':'contended shared host'}
    directory.mkdir(exist_ok=False);audit.write(directory/'contract.json',contract)
    with (directory/'inventory.jsonl').open('w') as f:
        for r in inventory:f.write(json.dumps(r)+'\n')
    return {'inventory':len(raw),'eligible':len(entries),'test_artifacts':len(test_files)}


def check(directory):
    contract=json.loads((directory/'contract.json').read_text())
    for p,h in contract['files_sha256'].items():
        if audit.sha(LANE_ROOT/p)!=h:raise ValueError('Frozen refresh dependency changed: '+p)
    if audit.digest(audit.rows(directory/'inventory.jsonl'))!=contract['inventory_sha256']:raise ValueError('Inventory drift')
    raw,entries,problems,boundary=audit.inputs()
    if audit.digest(boundary)!=contract['boundary_sha256']:raise ValueError('Protected boundary drift')
    return contract,entries,problems


def _validate_rows(rows,keys):
    seen={r['key'] for r in rows}
    if len(seen)!=len(rows) or not seen<=keys:raise ValueError('Invalid resume identities')
    return seen


def run(directory,max_items=4000,wall_seconds=240):
    if not 0<max_items<=4000 or not 0<wall_seconds<=270:raise ValueError('Unsupported refresh chunk budget')
    print(f'[run-contract] run_name={directory.name} device=cpu threads=2 memory=2GiB generation=false timing=contended',flush=True)
    start=time.monotonic();contract,entries,problems=check(directory);keys={e.key for e in entries};inventory={r['key']:r for r in audit.rows(directory/'inventory.jsonl')}
    public_path=directory/'public.jsonl';public=_rows(public_path);done=_validate_rows(public,keys);count=0
    class NoEmbedding:
        def encode(self,*args,**kwargs):raise AssertionError('Exact catalog refresh attempted model inference')
    allkeys=json.loads(corpus.KEYS_PATH.read_text());indices=[i for i,k in enumerate(allkeys) if k in keys]
    context=Context(generator=None,embedder=NoEmbedding(),lookup=LookupIndex(entries,np.load(corpus.EMBEDDINGS_PATH)[indices]),
        thresholds=load_thresholds(),classifier=None,entries=entries,budget=Budget.from_contract(json.loads((LANE_ROOT/'contracts/run_contract.json').read_text())))
    for e in entries:
        if e.key in done:continue
        if count>=max_items or time.monotonic()-start>=wall_seconds:break
        q,receipt=query_for(e,problems)
        if audit.digest(q.public_tests)!=inventory[e.key]['public_sha256']:raise ValueError('Query examples drift')
        result=answer(context,q,public_output_contracts=POLICY['public_output_contracts'])
        row={'key':e.key,'entry_sha256':entry_hash(e),'input_repair':receipt,'result':result}
        _append(public_path,row);public.append(row);done.add(e.key);count+=1
        if len(done)%100==0:print(f'[public] {len(done)}/{len(keys)}',flush=True)
    if done!=keys:return summarize(directory)
    seal_path=directory/'public-seal.json';seal={'sha256':audit.sha(public_path),'count':len(public)}
    if seal_path.exists() and json.loads(seal_path.read_text())!=seal:raise ValueError('Public decision seal changed')
    if not seal_path.exists():audit.write(seal_path,seal)
    scores_path=directory/'answers.jsonl';scores=_rows(scores_path);scored=_validate_rows(scores,keys);bykey={e.key:e for e in entries}
    for row in public:
        if row['key'] in scored:continue
        if count>=max_items or time.monotonic()-start>=wall_seconds:break
        e=bykey[row['key']];r=row['result'];ref=selected_reference(e);accepted=r['decision']=='answered';identity=(r.get('match') or {}).get('key')==e.key
        for tests in inventory[e.key]['independent_test_sets']:
            path=Path(tests['path']);path=path if path.is_absolute() else DERIVED/path
            if audit.sha(path)!=contract['test_artifact_sha256'][str(path.resolve())]:raise ValueError('Independent artifact drift')
        stored=audit.independent_score(e,ref['code'],problems,inventory[e.key])
        returned=(stored if r.get('code')==ref['code'] else
                  audit.independent_score(e,r.get('code'),problems,inventory[e.key]))
        result={k:v for k,v in r.items() if k!='code'};result['code_sha256']=code_hash(r['code']) if r.get('code') else None
        output={'key':e.key,'accepted_and_correct':bool(accepted and identity and returned['status']=='passed'),
                'stored_solution':stored,'returned_solution':returned,'result':result,'identity_correct':identity,
                'accepted':accepted,'fresh_execution':True}
        _append(scores_path,output);scored.add(e.key);count+=1
        if len(scored)%100==0:print(f'[independent] {len(scored)}/{len(keys)}',flush=True)
    return summarize(directory)


def import_public(directory,source):
    """Reuse only fresh sealed public decisions across a scoring-only revision."""
    current,entries,_=check(directory)
    old=json.loads((source/'contract.json').read_text())
    driver='algsolve/catalog_refresh.py'
    for field in ['runtime_files_sha256','test_artifact_sha256','inventory_sha256','answer_policy','boundary_sha256','eligible']:
        if old[field]!=current[field]:raise ValueError('Public import binding differs: '+field)
    old_inputs={k:v for k,v in old['files_sha256'].items() if k!=driver}
    new_inputs={k:v for k,v in current['files_sha256'].items() if k!=driver}
    if old_inputs!=new_inputs:raise ValueError('Public import inputs differ')
    archived=source/'catalog_refresh-frozen-v1.py'
    if audit.sha(archived)!=old['files_sha256'][driver]:raise ValueError('Original scoring driver missing')
    rows=audit.rows(source/'public.jsonl');seal=json.loads((source/'public-seal.json').read_text())
    if seal!={'sha256':audit.sha(source/'public.jsonl'),'count':len(rows)}:raise ValueError('Public import seal differs')
    if _validate_rows(rows,{e.key for e in entries})!={e.key for e in entries}:raise ValueError('Public import incomplete')
    bykey={e.key:e for e in entries}
    if any(r['entry_sha256']!=entry_hash(bykey[r['key']]) for r in rows):raise ValueError('Public import entry differs')
    for name in ['public.jsonl','public-seal.json']:
        with (directory/name).open('xb') as target:target.write((source/name).read_bytes())
    receipt={'source_contract_sha256':audit.sha(source/'contract.json'),'current_contract_sha256':audit.sha(directory/'contract.json'),
             'public_sha256':seal['sha256'],'count':len(rows),'independent_verdicts_reused':0,
             'changed_dependency':driver,'reason':'Scoring scope correction only; all serving/query/input bindings identical'}
    audit.write(directory/'public-import-receipt.json',receipt)
    return receipt


def summarize(directory):
    contract=json.loads((directory/'contract.json').read_text());public=_rows(directory/'public.jsonl');scores=_rows(directory/'answers.jsonl')
    result={'eligible':contract['eligible'],'public_completed':len(public),'independent_classified':len(scores),
            'fresh_correct':sum(r['accepted_and_correct'] for r in scores),
            'independent_status':dict(Counter(r['stored_solution']['status'] for r in scores)),
            'complete':len(scores)==contract['eligible'],'old_approval_reused':False}
    audit.write(directory/'summary.json',result);return result


def build_catalog(directory):
    contract,entries,_=check(directory);scores=_rows(directory/'answers.jsonl')
    if _validate_rows(scores,{e.key for e in entries})!={e.key for e in entries}:raise ValueError('Incomplete refresh cannot publish a catalog')
    seal=json.loads((directory/'public-seal.json').read_text())
    if audit.sha(directory/'public.jsonl')!=seal['sha256']:raise ValueError('Public seal drift')
    manifest=build(entries,audit.rows(directory/'inventory.jsonl'),scores,
        evidence={name:audit.sha(directory/name) for name in ['contract.json','inventory.jsonl','public-seal.json','answers.jsonl']},
        runtime_files=contract['runtime_files_sha256'],answer_policy=POLICY)
    target=directory/'approved-library.json'
    if target.exists():raise ValueError('Catalog already exists; preserve it')
    audit.write(target,manifest);return manifest['counts']


def verify(directory,max_items=4000,wall_seconds=240):
    start=time.monotonic();contract,entries,problems=check(directory)
    context,catalog=load_context(directory/'approved-library.json')
    path=directory/'verified.jsonl';rows=_rows(path);done=_validate_rows(rows,{e.key for e in entries});count=0
    for e in entries:
        if e.key in done:continue
        if count>=max_items or time.monotonic()-start>=wall_seconds:break
        q,_=query_for(e,problems);r=answer(context,q,approved_library=catalog)
        approved=e.key in catalog.manifest['approved'];expected=catalog.manifest['approved'].get(e.key,{})
        passed=(r['decision']=='answered' and r.get('code') and code_hash(r['code'])==expected['code_sha256'] and
                r.get('example_passed') and (r.get('match') or {}).get('key')==e.key) if approved else r['decision']=='abstain' and r.get('code') is None
        out={'key':e.key,'approved':approved,'passed':bool(passed),'decision':r['decision'],'reason':r.get('reason'),'seconds':r['seconds']}
        _append(path,out);rows.append(out);done.add(e.key);count+=1
        if len(done)%100==0:print(f'[serving] {len(done)}/{len(entries)}',flush=True)
    result={'eligible':len(entries),'complete':len(done)==len(entries),'verified':len(rows),
            'approved_answered':sum(r['approved'] and r['passed'] for r in rows),
            'excluded_abstained':sum(not r['approved'] and r['passed'] for r in rows),
            'failures':[r for r in rows if not r['passed']], 'encoder_loaded':context.embedder.encoder is not None}
    audit.write(directory/'serving-summary.json',result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['freeze','run','build','verify','summary']);p.add_argument('--name',required=True)
    p.add_argument('--max-items',type=int,default=4000);p.add_argument('--wall-seconds',type=float,default=240);a=p.parse_args()
    if not a.name.replace('-','').isalnum():raise ValueError('Invalid name')
    directory=LANE_ROOT/'runs'/a.name
    if a.action in ('run','verify'):result={'run':run,'verify':verify}[a.action](directory,a.max_items,a.wall_seconds)
    else:result={'freeze':freeze,'build':build_catalog,'summary':summarize}[a.action](directory)
    print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
