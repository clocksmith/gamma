"""Frozen public-parser development comparison; never reads protected examples/tests."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import time
from unittest.mock import patch

import numpy as np
from algsolve import corpus, importers, library_audit as audit
from algsolve.answer import answer
from algsolve.lookup import LookupIndex, load_thresholds
from algsolve.routes import Budget, Context

ROOT = audit.LANE_ROOT
OUT = ROOT / 'runs/known-problem-1a-128-v1'
REPORT = Path(__file__).parent

def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

def main():
    signal.alarm(300)
    started = time.monotonic()
    OUT.mkdir(exist_ok=False)
    control_path = Path('/tmp/gamma-1a-control-importers.py')
    control_bytes = control_path.read_bytes()
    (OUT/'control-importers.py').write_bytes(control_bytes)
    spec = importlib.util.spec_from_file_location('algsolve.control_importers', OUT/'control-importers.py')
    control = importlib.util.module_from_spec(spec); spec.loader.exec_module(control)
    raw, entries, problems, boundary = audit.inputs()
    manifest_path = ROOT/'findings/known-lookup-release-v2/approved-library.json'
    manifest = json.loads(manifest_path.read_text())
    inv_path = ROOT/'findings/library-answer-audit-v2/inventory.jsonl'
    inventory = {r['key']:r for r in audit.rows(inv_path)}
    selected = [e for e in entries if manifest['excluded'].get(e.key) == 'exact_answer_path_not_qualified'
                and inventory[e.key]['public_examples'] == 0]
    files = [Path(__file__), ROOT/'algsolve/importers.py', ROOT/'algsolve/public_examples.py',
             ROOT/'algsolve/answer.py', corpus.ENTRIES_PATH, corpus.KEYS_PATH, corpus.EMBEDDINGS_PATH,
             manifest_path, inv_path, ROOT/'contracts/run_contract.json']
    contract = {'schema':'algsolve.known-parser-development.v1',
                'scope':'1a exact stored-answer public-example recovery; development only, no release promotion',
                'selection':'all eligible exact_answer_path_not_qualified entries with zero recorded public examples',
                'cases':[e.key for e in selected], 'inventory':len(raw), 'eligible':len(entries),
                'protected_excluded':len(boundary['keys']), 'boundary_sha256':audit.digest(boundary),
                'source_sha256':{str(p.relative_to(ROOT)):audit.sha(p) for p in files},
                'control_importers_sha256':hashlib.sha256(control_bytes).hexdigest(),
                'budgets':{'run_wall_seconds':300,'threads':2,'memory_bytes':6*1024**3,'disk_bytes':1024**3,
                           'route_seconds':120,'public_judge_seconds':30,'independent_seconds':30},
                'no_model_inference':True,'timing':'contended shared host; no latency qualification',
                'seal':'all public decisions written and hashed before any independent test load',
                'acceptance':'at least one additional exact answer passes all available independent checks; zero changed existing parse results; zero wrong accepted answers'}
    write(OUT/'contract.json', contract)
    # Data-only census; no code execution or independent test payloads.
    census = []
    for e in entries:
        primary, _ = audit.original_for(e, problems)
        with patch.object(importers, 'statement_examples', control.statement_examples):
            old = audit.exact_query(e, primary)
        new = audit.exact_query(e, primary)
        if old.public_tests != new.public_tests:
            census.append({'key':e.key,'old_count':len(old.public_tests),'new_count':len(new.public_tests),
                           'previously_nonempty':bool(old.public_tests)})
    write(OUT/'parser-census.json', {'eligible':len(entries),'changed':census})
    keys = json.loads(corpus.KEYS_PATH.read_text()); blocked=set(boundary['keys'])
    assert keys == [r['key'] for r in raw]
    vectors=np.load(corpus.EMBEDDINGS_PATH)[[i for i,k in enumerate(keys) if k not in blocked]]
    class NoEmbedding:
        def encode(self, *args, **kwargs):
            raise AssertionError('Exact statement/interface unexpectedly requested model inference')
    ctx=Context(generator=None,embedder=NoEmbedding(),lookup=LookupIndex(entries,vectors),
                thresholds=load_thresholds(),classifier=None,entries=entries,
                budget=Budget.from_contract(json.loads((ROOT/'contracts/run_contract.json').read_text())))
    decisions=[]
    for e in selected:
        primary,_=audit.original_for(e,problems)
        for arm, parser in [('control',control.statement_examples),('candidate',importers.statement_examples)]:
            with patch.object(importers,'statement_examples',parser):
                q=audit.exact_query(e,primary)
                result=answer(ctx,q)
            decisions.append({'key':e.key,'arm':arm,'result':result})
            print(e.key,arm,result['decision'],result.get('reason',''),flush=True)
    write(OUT/'decisions.json',decisions)
    write(OUT/'decisions-seal.json',{'sha256':audit.sha(OUT/'decisions.json'),'count':len(decisions)})
    # Only now read independent tests for returned outputs, never selection.
    by_key={e.key:e for e in selected}; scored=[]
    for row in decisions:
        r=row['result']; e=by_key[row['key']]
        score=audit.independent_score(e,r.get('code'),problems,inventory[e.key])
        scored.append({'key':e.key,'arm':row['arm'],'decision':r['decision'],
                       'reason':r.get('reason'),'public_examples':r['public_example_count'],
                       'identity_correct':r.get('source',{}).get('key')==e.key,
                       'seconds':r['seconds'],'independent':score})
    write(OUT/'scores.json',scored)
    arms={}
    for arm in ('control','candidate'):
        rows=[r for r in scored if r['arm']==arm]
        arms[arm]={'cases':len(rows),'accepted':sum(r['decision']=='answered' for r in rows),
                   'accepted_and_correct':sum(r['decision']=='answered' and r['identity_correct'] and r['independent']['status']=='passed' for r in rows),
                   'wrong_acceptance':sum(r['decision']=='answered' and (not r['identity_correct'] or r['independent']['status']=='failed') for r in rows),
                   'abstentions':sum(r['decision']!='answered' for r in rows)}
    summary={'arms':arms,'parser_census':{'eligible':len(entries),'changed':len(census),
             'previously_nonempty_changed':sum(r['previously_nonempty'] for r in census)},
             'rows':scored,'wall_seconds':time.monotonic()-started,'timing':'contended',
             'release_promotion':False,'protected_scored':False,'model_inference':False,
             'approval_catalog_unchanged':True,'catalog_counts':manifest['counts']}
    write(OUT/'summary.json',summary)
    for name in ['contract.json','parser-census.json','decisions-seal.json','summary.json']:
        (REPORT/name).write_bytes((OUT/name).read_bytes())
    print(json.dumps(arms),flush=True)
if __name__=='__main__':main()
