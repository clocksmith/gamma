"""Consumed-development comparison: real frozen retrieval, approval and judge.

Run with the approval-bound isolated runtime on PYTHONPATH. Three arms: unchanged answer, old contradiction filter, and no-action option. Every arm performs
its own actual embedding/retrieval. Decisions seal before source-test scoring.
"""
import copy
from dataclasses import replace
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import sys
import time

from algsolve import validate
from algsolve.answer import answer
from algsolve.approved_library import ApprovedLibrary
from algsolve.embed import Embedder, EMBEDDING_DIR
from algsolve.lookup import LookupIndex
from algsolve.records import LANE_ROOT as RUNTIME, Problem
from algsolve.requirement_filter import RequirementFilter, answer_with_policy
from algsolve.routes import Context, Budget
from algsolve.splits import IndexEntry
from algsolve.rebuild_recognition import Monitor, publish, sha, digest

ROOT = Path(os.environ['ALGSOLVE_EXPERIMENT_ROOT'])
CONTROL = ROOT / 'runs/recognition-rebuild-dev-suby-v1'
OUT = ROOT / 'runs/noop-option-real-dev-128-v1'
load = lambda path: json.loads(path.read_text())


def files(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


class Recording:
    def __init__(self, encoder, lookup):
        self.encoder, self.lookup = encoder, lookup
        self.trace = {'embedding_seconds': 0., 'retrieval_seconds': 0., 'vectors': [], 'candidates': []}

    def __getattr__(self, name):
        return getattr(self.lookup, name)

    def encode(self, texts, **kwargs):
        started = time.perf_counter()
        vectors = self.encoder.encode(texts, **kwargs)
        self.trace['embedding_seconds'] += time.perf_counter()-started
        self.trace['vectors'].append(hashlib.sha256(vectors.tobytes()).hexdigest())
        return vectors

    def scored_candidates(self, text, vector):
        started = time.perf_counter()
        candidates = self.lookup.scored_candidates(text, vector)
        self.trace['retrieval_seconds'] += time.perf_counter()-started
        self.trace['candidates'] = copy.deepcopy(candidates)
        return candidates


def main():
    import numpy as np
    import torch
    if OUT.exists():
        raise ValueError('New run only; preserve prior attempt and use a separately named recovery')
    OUT.mkdir()
    before = files(CONTROL)
    for name, expected in load(CONTROL/'summary.json')['artifacts_sha256'].items():
        assert sha(CONTROL/name) == expected, name
    assert sha(CONTROL/'candidate.json') == '64f10768b5004782cf8549215357d8d08ee2be8cd74b8b6198fe8c7ced83a33e'
    approved = ApprovedLibrary.load(CONTROL/'approved-library.json')
    approved.verify_runtime(RUNTIME)
    entries = [IndexEntry(**e) for e in load(CONTROL/'qualified-entries.json')]
    fixtures = load(CONTROL/'fixtures.json')
    vectors = np.stack([np.load(CONTROL/f'embeddings/{i:04d}.npy', allow_pickle=False) for i in range(len(entries))])
    assert vectors.shape == (66,1024) and len(fixtures) == 24 and np.isfinite(vectors).all()
    gate_path = ROOT/'contracts/clarification_profiles_v1.json'
    baseline = RequirementFilter(load(gate_path)['profiles'])
    candidate_policy = RequirementFilter(load(gate_path)['profiles'], allow_noop_option=True)
    snapshot = {str(p.relative_to(RUNTIME)): sha(p) for p in sorted((RUNTIME/'algsolve').rglob('*.py'))}
    candidate = dict(name=OUT.name, scope='consumed development; no promotion or tuning',
                     control_files_sha256=before, runtime_sources_sha256=snapshot,
                     profiles_sha256=sha(gate_path), driver_sha256=sha(Path(__file__)),
                     encoder_files_sha256={n: sha(EMBEDDING_DIR/n) for n in ['model.safetensors','tokenizer.json','config.json','tokenizer_config.json']},
                     dependencies={n: importlib.metadata.version(n) for n in ['torch','transformers','numpy']},
                     interpreter=sys.executable, runtime=str(RUNTIME),
                     control='Unchanged answer() with original approval catalog and66 cached source vectors',
                     baseline='Existing contradiction filter with unchanged conservative extraction',
                     candidate='Same contradiction filter plus opt-in trailing no-action transaction alternative; rejected required-facet gate not used',
                     accounting='Fresh real embedding/retrieval each arm, alternating order; warm full route wall measured directly. Model load separately reported. Independent scoring excluded from route.',
                     limits=dict(cpu_threads=4, rss_bytes=8*1024**3,disk_bytes=5*1024**3,wall_seconds=900),
                     training=False, protected_opened=False, questions=0)
    publish(OUT/'candidate.json', candidate)
    monitor = Monitor([CONTROL,OUT,EMBEDDING_DIR,RUNTIME], seconds=900)
    monitor.start()
    started = time.perf_counter()
    try:
        torch.set_num_threads(4); torch.set_num_interop_threads(1)
        assert torch.equal(torch.ones((2,2)) @ torch.ones((2,2)), torch.full((2,2),2.))
        print('[run-contract] run_name='+OUT.name+' pairs_input_spec=frozen66-index24-requests resume_from=none resume_stage=none decode=none eval_dataset_paths=consumed-development device=cpu schedule=alternating-paired runtime_mode=reviewed-linux-sandbox sweep_mode=live', flush=True)
        print(json.dumps(dict(python=sys.executable,cuda_available=torch.cuda.is_available(),cuda_count=torch.cuda.device_count(),device='cpu')),flush=True)
        load_start=time.perf_counter(); encoder=Embedder(device='cpu'); setup=time.perf_counter()-load_start
        lookup=LookupIndex(entries,vectors)
        budget=Budget.from_contract(load(RUNTIME/'contracts/run_contract.json'))
        pairs=[]
        for i, fixture in enumerate(fixtures):
            query=Problem.from_dict(fixture['query']);pair={};order=['control','baseline','candidate'] if i%2==0 else ['candidate','baseline','control']
            pair_started=time.perf_counter()
            for arm in order:
                recording=Recording(encoder,lookup)
                context=Context(generator=None,embedder=recording,lookup=recording,
                                thresholds=load(RUNTIME/'contracts/lookup_thresholds.json'),classifier=None,
                                entries=entries,budget=budget)
                context.statement_thresholds=load(RUNTIME/'contracts/statement_lookup_thresholds.json')
                tick=time.perf_counter()
                result=(answer(context,query,approved_library=approved) if arm=='control' else
                        answer_with_policy(context,query,approved,baseline if arm=='baseline' else candidate_policy))
                elapsed=time.perf_counter()-tick
                pair[arm]=dict(result=result,route_seconds=elapsed,retrieval=recording.trace,
                               within_budget=elapsed<=budget.route_wall_seconds)
                print(json.dumps(dict(id=fixture['id'],arm=arm,decision=result['decision'],reason=result.get('reason'),seconds=elapsed)),flush=True)
            # Do not hide backend nondeterminism behind an identical-input claim.
            a=pair['control']['retrieval']
            for arm in ('baseline','candidate'):
                b=pair[arm]['retrieval']
                assert a['vectors']==b['vectors'] and a['candidates']==b['candidates'], 'Retrieval drift between arms'
            pair['paired_wall_seconds']=time.perf_counter()-pair_started
            publish(OUT/f'response-{i:04d}.json',pair);pairs.append(pair)
        response_hashes={p.name:sha(p) for p in sorted(OUT.glob('response-*.json'))}
        publish(OUT/'decisions-seal.json',dict(candidate_sha256=sha(OUT/'candidate.json'),responses_sha256=response_hashes))
        source_tests=load(CONTROL/'source-tests.json');rows=[]
        for fixture,pair in zip(fixtures,pairs):
            row=dict(id=fixture['id'],kind=fixture['kind'])
            for arm in ('control','baseline','candidate'):
                result=pair[arm]['result'];accepted=result['decision']=='answered';key=fixture['expected_key'];verdict=None
                tick=time.perf_counter()
                if accepted and key in source_tests:
                    query=Problem.from_dict(fixture['query']);query.entry=result['answer_interface']
                    verdict=validate.judge_problem(query,result['code'],source_tests[key]['tests']).to_dict()
                identity=key is not None and result.get('match',{}).get('key')==key
                approval=(result.get('source') or {}).get('qualification',{}).get('approved',False)
                infra=any(a.get('public',{}).get('reason') in ('sandbox_error','checker_error') for a in result['attempts']) or bool(verdict and verdict['reason'] in ('sandbox_error','checker_error'))
                row[arm]=dict(accepted=accepted,correct=bool(accepted and identity and approval and verdict and verdict['passed']),
                              wrong=bool(accepted and (not identity or (verdict and not verdict['passed'] and not infra))),
                              unqualified=bool(accepted and (not approval or verdict is None)),infrastructure_error=infra,
                              abstained=not accepted,reason=result.get('reason'),route_seconds=pair[arm]['route_seconds'],
                              independent=verdict,scoring_seconds=time.perf_counter()-tick,within_budget=pair[arm]['within_budget'])
            rows.append(row)
        assert files(CONTROL)==before, 'Original control changed'
        assert snapshot=={str(p.relative_to(RUNTIME)):sha(p) for p in sorted((RUNTIME/'algsolve').rglob('*.py'))}, 'Runtime drift'
        def metrics(arm,selected):
            rs=[r[arm] for r in selected];ts=[r['route_seconds'] for r in rs]
            return dict(requests=len(rs),**{k:sum(r[k] for r in rs) for k in ['accepted','correct','wrong','unqualified','infrastructure_error','abstained']},
                        coverage=sum(r['accepted'] for r in rs)/len(rs),correct_coverage=sum(r['correct'] for r in rs)/len(rs),
                        latency_seconds=dict(p50=float(np.percentile(ts,50)),p95=float(np.percentile(ts,95)),maximum=max(ts)))
        drift=[]
        for i,row in enumerate(rows):
            old=load(CONTROL/f'scores/{i:04d}.json')['value'];new=row['control']
            if (old['accepted'],old['accepted_and_correct'],old['reason'])!=(new['accepted'],new['correct'],new['reason']):drift.append(row['id'])
        report=dict(name=OUT.name,overall={a:metrics(a,rows) for a in ['control','baseline','candidate']},
                    specified={a:metrics(a,[r for r in rows if r['kind'] in ['informal','changed_signature']]) for a in ['control','baseline','candidate']},
                    rows=rows,correct_answers_lost=[r['id'] for r in rows if r['control']['correct'] and not r['candidate']['correct']],
                    wrong_acceptances_blocked=[r['id'] for r in rows if r['control']['wrong'] and not r['candidate']['wrong']],
                    control_drift=drift,setup_seconds=setup,actual_run_wall_seconds=time.perf_counter()-started,
                    resources=monitor.counters(),candidate_sha256=sha(OUT/'candidate.json'),
                    original_control_preserved=True,per_arm_retrieval_identical=True,
                    newly_correct_vs_baseline=[r['id'] for r in rows if r['candidate']['correct'] and not r['baseline']['correct']],
                    lost_correct_vs_baseline=[r['id'] for r in rows if r['baseline']['correct'] and not r['candidate']['correct']],
                    limitations=['Consumed development only','Finite source tests, not independent query qualification','CPU latency under existing Reploid host load; no exclusive-host claim','No release promotion or candidate tuning'])
        publish(OUT/'summary.json',report)
        print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2),flush=True)
    except BaseException as error:
        publish(OUT/'failure.json',dict(error=type(error).__name__,detail=str(error),resources=monitor.counters()))
        raise
    finally:
        monitor.stop.set()


if __name__=='__main__':
    main()
