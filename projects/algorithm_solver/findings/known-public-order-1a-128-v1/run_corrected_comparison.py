"""All100 eligible exact-path gaps; public-order candidate vs unchanged control."""
import json
from collections import Counter
from pathlib import Path
import signal
import time
import numpy as np
from algsolve import corpus, library_audit as audit, validate
from algsolve.answer import answer
from algsolve.lookup import LookupIndex, load_thresholds
from algsolve.public_contracts import bind, unordered_outer_declared
from algsolve.routes import Budget, Context
ROOT=audit.LANE_ROOT
REPORT=Path(__file__).parent/'corrected-v2'
OUT=ROOT/'runs/known-public-order-1a-128-v2'
write=audit.write

def main():
    signal.alarm(300);started=time.monotonic();OUT.mkdir(exist_ok=False);REPORT.mkdir(exist_ok=False)
    raw,entries,problems,boundary=audit.inputs();blocked=set(boundary['keys'])
    catalog_path=ROOT/'findings/known-lookup-release-v2/approved-library.json'
    catalog=json.loads(catalog_path.read_text());invpath=ROOT/'findings/library-answer-audit-v2/inventory.jsonl'
    inventory={r['key']:r for r in audit.rows(invpath)}
    selected=[e for e in entries if catalog['excluded'].get(e.key)=='exact_answer_path_not_qualified']
    assert len(selected)==100
    deps=['answer.py','public_contracts.py','public_examples.py','importers.py','values.py','validate.py',
          'lookup.py','records.py','routes.py','library_audit.py','splits.py','recognition_boundary.py']
    files=[Path(__file__),catalog_path,invpath,corpus.ENTRIES_PATH,corpus.KEYS_PATH,corpus.EMBEDDINGS_PATH,
           ROOT/'contracts/run_contract.json',ROOT/'contracts/lookup_thresholds.json']
    files += [ROOT/'algsolve'/f for f in deps]+list((ROOT/'algsolve/judge').glob('*.py'))
    contract={'schema':'algsolve.public-order-development.v1','scope':'exact stored-answer development only',
              'selection':'all100 eligible exact_answer_path_not_qualified catalog entries, no score-based selection',
              'keys':[e.key for e in selected],'inventory':len(raw),'eligible':len(entries),
              'protected_entries_present':len(raw)-len(entries),'protected_closure_keys':len(blocked),
              'boundary_sha256':audit.digest(boundary),'files_sha256':{str(p.relative_to(ROOT)):audit.sha(p) for p in files},
              'budgets':{'run_wall_seconds':300,'threads':2,'memory_bytes':6*1024**3,'disk_bytes':1024**3,
                         'route_seconds':120,'public_judge_seconds':30,'independent_seconds':30},
              'policy':'opt-in complete explicit unordered-return clause before examples; existing host unordered_outer only',
              'acceptance':'positive new independently correct answers, zero wrong/harmful changes',
              'seal':'all200 public decisions sealed before independent test reads',
              'timing':'contended shared host; no latency qualification','model_inference':False}
    write(OUT/'contract.json',contract)
    cache=validate.load_cache();causes=[]
    for e in entries:
        reason=catalog['excluded'].get(e.key)
        if not reason:continue
        q=audit.exact_query(e,audit.original_for(e,problems)[0])
        cause=reason
        if reason=='exact_answer_path_not_qualified':
            cause=('no_recovered_public_examples' if not q.public_tests else
                   'explicit_unordered_outer_declaration' if unordered_outer_declared(q.statement) else
                   'other_public_execution_or_output_contract')
        elif reason=='failed':
            failures=[cache.get(u,{}) for u in e.members if u.startswith('lcd:')]
            metadata=json.dumps([{k:r.get(k) for k in ('hidden_failure','stderr_tail')} for r in failures])
            cause=('missing_sortedcontainers_or_SortedList' if 'SortedList' in metadata or 'sortedcontainers' in metadata else
                   'memory_error_under_frozen_limits' if 'MemoryError' in metadata else
                   'missing_datetime_import' if 'datetime' in metadata else 'unclassified_stored_runtime_failure')
        elif reason=='unusable_imported_evidence':cause='in_place_dataset_checks_only_None_return'
        causes.append({'key':e.key,'historical_exclusion':reason,'concrete_cause':cause})
    write(OUT/'coverage-causes.json',{'eligible':len(entries),'historical_approved':len(catalog['approved']),
          'excluded_eligible':len(causes),'historical_counts':dict(Counter(r['historical_exclusion'] for r in causes)),
          'concrete_counts':dict(Counter(r['concrete_cause'] for r in causes)),'rows':causes,
          'limits':'runtime causes are historical metadata; selected100 paths freshly executed below'})
    keys=json.loads(corpus.KEYS_PATH.read_text());assert keys==[r['key'] for r in raw]
    vectors=np.load(corpus.EMBEDDINGS_PATH)[[i for i,k in enumerate(keys) if k not in blocked]]
    class NoEmbedding:
        def encode(self,*args,**kwargs):raise AssertionError('Exact lookup requested model inference')
    ctx=Context(generator=None,embedder=NoEmbedding(),lookup=LookupIndex(entries,vectors),thresholds=load_thresholds(),
                classifier=None,entries=entries,budget=Budget.from_contract(json.loads((ROOT/'contracts/run_contract.json').read_text())))
    decisions=[]
    for i,e in enumerate(selected):
        q=audit.exact_query(e,audit.original_for(e,problems)[0])
        for arm,optin in [('control',False),('candidate',True)]:
            r=answer(ctx,q,public_output_contracts=optin)
            decisions.append({'key':e.key,'arm':arm,'contract_applied':bind(q).public_tests!=q.public_tests if optin else False,'result':r})
        print(f'[public] {i+1}/100 {e.key} '+str([r['result']['decision'] for r in decisions[-2:]]),flush=True)
    write(OUT/'decisions.json',decisions);write(OUT/'decisions-seal.json',{'sha256':audit.sha(OUT/'decisions.json'),'count':len(decisions)})
    by_key={e.key:e for e in selected};scores=[]
    for row in decisions:
        e=by_key[row['key']];r=row['result']
        scored=audit.independent_score(e,r.get('code'),problems,inventory[e.key])
        scores.append({'key':e.key,'arm':row['arm'],'decision':r['decision'],'reason':r.get('reason'),
                       'contract_applied':row['contract_applied'],'public_examples':r['public_example_count'],
                       'identity_correct':(r.get('source') or {}).get('key')==e.key,'seconds':r['seconds'],
                       'independent':scored,'code_sha256':None if not r.get('code') else __import__('hashlib').sha256(r['code'].encode()).hexdigest()})
    write(OUT/'scores.json',scores)
    def correct(r):return r['decision']=='answered' and r['identity_correct'] and r['independent']['status']=='passed'
    arms={}
    for arm in ('control','candidate'):
        rows=[r for r in scores if r['arm']==arm]
        arms[arm]={'cases':len(rows),'accepted':sum(r['decision']=='answered' for r in rows),
                   'correct':sum(correct(r) for r in rows),
                   'wrong':sum(r['decision']=='answered' and (not r['identity_correct'] or r['independent']['status']=='failed') for r in rows),
                   'abstain':sum(r['decision']!='answered' for r in rows)}
    pair={key:{r['arm']:r for r in scores if r['key']==key} for key in by_key}
    useful=[k for k,p in pair.items() if correct(p['candidate']) and not correct(p['control'])]
    harmful=[k for k,p in pair.items() if correct(p['control']) and not correct(p['candidate'])]
    for f,h in contract['files_sha256'].items():assert audit.sha(ROOT/f)==h,f
    summary={'arms':arms,'useful':useful,'harmful':harmful,'rows':scores,'wall_seconds':time.monotonic()-started,
             'timing':'contended','release_promoted':False,'catalog_changed':False,'protected_scored':False,
             'development_signal':bool(useful) and not harmful and arms['candidate']['wrong']==0}
    write(OUT/'summary.json',summary)
    for name in ['contract.json','coverage-causes.json','decisions-seal.json','summary.json']:(REPORT/name).write_bytes((OUT/name).read_bytes())
    print(json.dumps({'arms':arms,'useful':useful,'harmful':harmful}),flush=True)
if __name__=='__main__':main()
