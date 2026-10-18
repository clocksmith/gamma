"""Calibrate and exercise description routes on existing development data only.

The original 24 descriptions remain unchanged. This writes a separate fixture
with explicit generic signatures and indexed public examples, not a claim about
natural requests supplying that information. Independent evaluation stays sealed.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import time

from . import corpus, validate
from .clarify import ClarificationSession, load_profiles
from .clarification_evaluation import load_dialogues
from .description_journey import DescriptionJourney, ROUTES
from .library_audit import inputs, original_for, exact_query, sha, digest, write
from .lookup import LookupIndex, fit_thresholds
from .records import LANE_ROOT, Problem, load_hidden_tests
from .requirements import extract
from .routes import Context, Budget


def load_context():
    import numpy as np
    import torch
    from .embed import Embedder
    torch.set_num_threads(4)
    print(f'cuda_available={torch.cuda.is_available()} device_count={torch.cuda.device_count()} target_device=cpu',flush=True)
    probe=torch.ones((2,2),device='cpu')
    if not torch.equal(probe@probe,torch.full((2,2),2.)):
        raise RuntimeError('CPU compute probe failed')
    raw,entries,problems,boundary=inputs()
    keys=json.loads(corpus.KEYS_PATH.read_text())
    if keys!=[r['key'] for r in raw]:raise ValueError('Corpus order changed')
    blocked=set(boundary['keys'])
    indices=[i for i,k in enumerate(keys) if k not in blocked]
    context=Context(generator=None,embedder=Embedder(device='cpu'),
        lookup=LookupIndex(entries,np.load(corpus.EMBEDDINGS_PATH)[indices]),thresholds={},classifier=None,
        entries=entries,budget=Budget.from_contract(json.loads((LANE_ROOT/'contracts/run_contract.json').read_text())))
    catalog=load_profiles()
    catalog['profiles']=[p for p in catalog['profiles'] if p['key'] in context.lookup.by_key]
    for p in catalog['profiles']:
        entry=entries[context.lookup.by_key[p['key']]]
        import hashlib
        if hashlib.sha256(entry.statement.encode()).hexdigest()!=p['statement_sha256']:
            raise ValueError('Profile source changed')
    return context,problems,catalog,boundary


def fixture(case, context, problems):
    original=None
    if case['expected_key']:
        entry=context.entries[context.lookup.by_key[case['expected_key']]]
        original,_=original_for(entry,problems)
        if original is None:raise ValueError('Missing development interface')
        public=exact_query(entry,original).public_tests
        params=[[f'arg{i}',p[1]] for i,p in enumerate(entry.params)]
    else:
        public=[]
        params=[]
    signature='class Solution:\n    def solve(self'+''.join(', '+p[0]+': '+p[1] for p in params)+'): ...'
    query=Problem('development:'+case['id'],'user',case['id'],'Development request','',case['query'],
                   'functional',starter_code=signature,entry={'class':'Solution','method':'solve'},
                   params=params,public_tests=public)
    return query,original


def calibrate(context,catalog,cases,fixtures):
    tables={'embedding_only':[], 'requirement_selection':[]}
    records=[]
    profiles={p['key']:p for p in catalog['profiles']}
    for case,(query,_) in zip(cases,fixtures):
        text=query.query_text()
        vector=context.embedder.encode([text],query=True)[0]
        candidates=sorted([dict(c,score=c['cosine']) for c in context.lookup.scored_candidates(text,vector)],
                           key=lambda c:(-c['score'],c['key']))
        # Ambiguous initial requests must not be trained as already-resolved.
        truth=case['expected_key'] if case['kind']!='underspecified' else None
        tables['embedding_only'].append((candidates,truth))
        requirements=extract(query.statement)
        supported=[]
        if not requirements['conflicts']:
            session=ClarificationSession(query.statement,candidates,catalog,facts=requirements['facts'])
            supported=[c for c in candidates if c['key'] in session.active and
                       all(requirements['facts'].get(f)==v for f,v in profiles[c['key']]['facts'].items())]
        if supported:tables['requirement_selection'].append((supported,truth))
        records.append({'id':case['id'],'candidates':candidates,'requirements':requirements,
                        'supported_candidates':supported,'calibration_truth':truth})
    thresholds={route:fit_thresholds(data) if data else {'min_score':1.000001,'min_margin':0.,'dev_cases':0}
                for route,data in tables.items()}
    return thresholds,records


def drive(journey, answers, confirmation):
    step=journey.start()
    while step['decision'] in ('clarify','confirm'):
        value=answers.get(step['facet'],'unsure') if step['decision']=='clarify' else confirmation
        if value not in {o['value'] for o in step['options']}:value='other'
        step=journey.reply(step['question_id'],value,
                           reviewed_statement_sha256=step.get('candidate',{}).get('statement_sha256'))
    return step


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name',required=True)
    args=parser.parse_args()
    if not args.name.replace('-','').replace('_','').isalnum():raise ValueError('Invalid name')
    directory=LANE_ROOT/'runs'/args.name
    if directory.exists():raise ValueError('Use a fresh run name')
    print(f'[run-contract] run_name={args.name} pairs_input_spec=existing-description-development '
          'resume_from=none resume_stage=none decode=none eval_dataset_paths=development-only '
          'device=cpu schedule=serial runtime_mode=cpu+linux-sandbox sweep_mode=after_train',flush=True)
    started=time.perf_counter()
    context,problems,catalog,boundary=load_context()
    load_seconds=time.perf_counter()-started
    _,all_cases=load_dialogues()
    excluded=[c['id'] for c in all_cases if c['expected_key'] and c['expected_key'] not in context.lookup.by_key]
    cases=[c for c in all_cases if c['id'] not in excluded]
    fixtures=[fixture(case,context,problems) for case in cases]
    directory.mkdir(parents=True,exist_ok=False)
    write(directory/'fixtures.json',[{'id':case['id'],'query':json.loads(query.to_json()),
                                     'public_source':original.uid if original else None}
                                    for case,(query,original) in zip(cases,fixtures)])
    thresholds,calibration=calibrate(context,catalog,cases,fixtures)
    write(directory/'thresholds.json',thresholds)
    write(directory/'calibration.json',calibration)
    sources={str(p.relative_to(LANE_ROOT)):sha(p) for p in sorted((LANE_ROOT/'algsolve').rglob('*.py'))}
    write(directory/'contract.json',{'partition':'development','sources':sources,
        'excluded_development_cases':excluded, 'exclusion_reason':'protected composition identity or alias',
        'thresholds_sha256':sha(directory/'thresholds.json'),'fixtures_sha256':sha(directory/'fixtures.json'),
        'boundary_sha256':digest(boundary),'embedding_load_seconds':load_seconds,
        'data':{p.name:sha(p) for p in (corpus.ENTRIES_PATH,corpus.KEYS_PATH,corpus.EMBEDDINGS_PATH)},
        'generation':False,'threshold_fit':'existing development only; ambiguous initial inputs labelled unresolved',
        'limits':['Generated development fixtures add original indexed public examples and generic solve signatures.',
                  'No independent query opened; this is development fitting, not generalization.',
                  'Scripted confirmations are not human understanding; missing examples cannot pass.',
                  'Machine is shared with the active baseline audit; timing is diagnostic, not matched performance evidence.']})
    results=[]
    with (directory/'journeys.jsonl').open('x') as stream:
        for route in ROUTES:
            for case,(query,original) in zip(cases,fixtures):
                journey=DescriptionJourney(context,query,catalog,thresholds,route=route)
                result=drive(journey,case['answers'],case['confirmation'])
                independent=None
                if result['code'] and original:
                    tests=load_hidden_tests(original)
                    if tests:
                        # Scoring-only method alias, not a change to returned code.
                        method=original.entry['method']
                        source=result['code']+'\nSolution.'+method+' = Solution.solve\n'
                        independent=validate.judge_problem(original,source,tests).to_dict()
                accepted=result['decision']=='answered'
                identity=result['key']==case['expected_key'] and result['key'] is not None
                row={'id':case['id'],'route':route,'kind':case['kind'],'result':result,
                     'history':journey.session.history if journey.session else [],'independent':independent,
                     'accepted_and_correct':accepted and identity and bool(independent and independent['passed']),
                     'wrong_acceptance':accepted and (not identity or bool(independent and not independent['passed']))}
                results.append(row);stream.write(json.dumps(row)+'\n');stream.flush()
                print(f'[description] {route} {case["id"]}: {result["decision"]} {result["reason"]}',flush=True)
    summary={'partition':'development','routes':{},'protected_evaluation_opened':False,
             'contract_sha256':sha(directory/'contract.json'),'journeys_sha256':sha(directory/'journeys.jsonl')}
    for route in ROUTES:
        rs=[r for r in results if r['route']==route]
        summary['routes'][route]={'requests':len(rs),'returned_answers':sum(r['result']['decision']=='answered' for r in rs),
            'accepted_and_correct':sum(r['accepted_and_correct'] for r in rs),
            'wrong_acceptances':sum(r['wrong_acceptance'] for r in rs),
            'questions':sum(r['result']['questions'] for r in rs),
            'confirmations':sum(r['result']['confirmations'] for r in rs)}
    write(directory/'summary.json',summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
