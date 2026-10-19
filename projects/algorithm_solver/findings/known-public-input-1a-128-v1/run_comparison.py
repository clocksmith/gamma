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
from algsolve.imported_examples import repair
from algsolve.approved_library import code_hash, entry_hash
from algsolve.routes import Budget, Context
ROOT=audit.LANE_ROOT
REPORT=Path(__file__).parent
OUT=ROOT/'runs/known-public-input-1a-128-v1'
write=audit.write

def main():
    signal.alarm(300);started=time.monotonic();OUT.mkdir(exist_ok=False)
    raw,entries,problems,boundary=audit.inputs();blocked=set(boundary['keys'])
    catalog_path=ROOT/'findings/known-lookup-release-v2/approved-library.json'
    catalog=json.loads(catalog_path.read_text());invpath=ROOT/'findings/library-answer-audit-v2/inventory.jsonl'
    inventory={r['key']:r for r in audit.rows(invpath)}
    prior_path=ROOT/'findings/known-public-order-1a-128-v1/corrected-v2/summary.json'
    prior=json.loads(prior_path.read_text())
    remaining={r['key'] for r in prior['rows'] if r['arm']=='candidate' and r['decision']!='answered'}
    selected=[e for e in entries if e.key in remaining]
    assert len(selected)==79
    deps=['answer.py','public_contracts.py','imported_examples.py','public_examples.py','importers.py','values.py','validate.py',
          'lookup.py','records.py','routes.py','library_audit.py','splits.py','recognition_boundary.py']
    files=[Path(__file__),catalog_path,invpath,prior_path,corpus.ENTRIES_PATH,corpus.KEYS_PATH,corpus.EMBEDDINGS_PATH,
           ROOT/'contracts/run_contract.json',ROOT/'contracts/lookup_thresholds.json']
    files += [ROOT/'algsolve'/f for f in deps]+list((ROOT/'algsolve/judge').glob('*.py'))
    contract={'schema':'algsolve.public-input-development.v1','scope':'exact stored-answer development only',
              'selection':'all79 remaining eligible exact-path abstentions from prior frozen public-order development run',
              'keys':[e.key for e in selected],'inventory':len(raw),'eligible':len(entries),
              'protected_entries_present':len(raw)-len(entries),'protected_closure_keys':len(blocked),
              'boundary_sha256':audit.digest(boundary),'files_sha256':{str(p.relative_to(ROOT)):audit.sha(p) for p in files},
              'budgets':{'run_wall_seconds':300,'threads':2,'memory_bytes':6*1024**3,'disk_bytes':1024**3,
                         'route_seconds':120,'public_judge_seconds':30,'independent_seconds':30},
              'policy':'source-bound imported LCD public inputs only; complete literal reparse must exactly reproduce historical collapse for every old test field except args; never change expected values',
              'acceptance':'positive new independently correct answers, zero wrong/harmful changes',
              'seal':'all158 public decisions sealed before independent test reads',
              'timing':'contended shared host; no latency qualification','model_inference':False}
    write(OUT/'contract.json',contract)
    cache=validate.load_cache();dependency_rows=[]
    for e in entries:
        if catalog['excluded'].get(e.key)!='failed':continue
        metadata=json.dumps([cache.get(u,{}).get('hidden_failure') for u in e.members if u.startswith('lcd:')])
        if 'SortedList' not in metadata and 'sortedcontainers' not in metadata:continue
        dependency_rows.append({'key':e.key,'references':[{'uid':r['uid'],'code_sha256':code_hash(r['code']),
             'dependency_present':'SortedList' in r['code'] or 'sortedcontainers' in r['code']} for r in e.references]})
    assert len(dependency_rows)==15 and all(r['dependency_present'] for e in dependency_rows for r in e['references'])
    write(OUT/'dependency-alternatives.json',{'entries':15,'refs':sum(len(e['references']) for e in dependency_rows),
          'dependency_free_alternatives':0,'rows':dependency_rows,'scope':'existing indexed references only; no execution,downloads or new source'})
    def source_query(e,optin):
        original,_=audit.original_for(e,problems)
        receipt={'changed':False,'reason':'source_identity_or_interface_differs'}
        if (original is not None and original.statement==e.statement and original.entry==e.entry
                and original.params==e.params and original.starter_code==e.starter_code):
            changed,receipt=repair(original)
            if optin:original=changed
        return audit.exact_query(e,original),receipt
    census=[]
    for e in entries:
        _,receipt=source_query(e,True)
        if receipt['changed']:census.append({'key':e.key,**receipt})
    write(OUT/'input-census.json',{'eligible':len(entries),'changed':len(census),'rows':census})
    keys=json.loads(corpus.KEYS_PATH.read_text());assert keys==[r['key'] for r in raw]
    vectors=np.load(corpus.EMBEDDINGS_PATH)[[i for i,k in enumerate(keys) if k not in blocked]]
    class NoEmbedding:
        def encode(self,*args,**kwargs):raise AssertionError('Exact lookup requested model inference')
    ctx=Context(generator=None,embedder=NoEmbedding(),lookup=LookupIndex(entries,vectors),thresholds=load_thresholds(),
                classifier=None,entries=entries,budget=Budget.from_contract(json.loads((ROOT/'contracts/run_contract.json').read_text())))
    decisions=[]
    for i,e in enumerate(selected):
        for arm,optin in [('control',False),('candidate',True)]:
            q,receipt=source_query(e,optin)
            r=answer(ctx,q,public_output_contracts=True)
            decisions.append({'key':e.key,'arm':arm,'contract_applied':receipt['changed'] if optin else False,
                              'repair_receipt':receipt,'entry_sha256':entry_hash(e),'result':r})
        print(f'[public] {i+1}/79 {e.key} '+str([r['result']['decision'] for r in decisions[-2:]]),flush=True)
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
    for name in ['contract.json','dependency-alternatives.json','input-census.json','decisions-seal.json','summary.json']:(REPORT/name).write_bytes((OUT/name).read_bytes())
    print(json.dumps({'arms':arms,'useful':useful,'harmful':harmful}),flush=True)
if __name__=='__main__':main()
