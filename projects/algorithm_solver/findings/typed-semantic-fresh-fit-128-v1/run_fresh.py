"""Single frozen fit experiment with actual inference and bounded literal repair.

Repair receives public inputs and captured logits only. The nearest baseline and
model memory use the same permitted fit library. Independent tests enter after
all route decisions are sealed. No training or protected evaluation.
"""
import copy
import importlib.metadata
import json
from pathlib import Path
import sys
import time

import numpy as np
import torch

from algsolve import validate
from algsolve.embed import Embedder, EMBEDDING_DIR
from algsolve.records import LANE_ROOT as ROOT, load_hidden_tests
from algsolve.rebuild_recognition import Monitor, sha, publish
from algsolve.synth import typed_codec, typed_confirmation, development_tests, mine
from algsolve.synth.train_typed import problem_for, query_text, INSTRUCTION
from algsolve.synth.typed_prediction_codec import PredictionCodec
from algsolve.synth.typed_predictor import TypedPredictor, decisions
from algsolve.synth.typed_comparison import run_route, nearest_graph, score_fixed
from algsolve.synth.typed_literal_repair import run_literal_route
from algsolve.synth.typed_semantic_repair import run_semantic_route

PROPOSAL = ROOT/'findings/typed-fit-semantic-diagnosis-128-v1/literal-construction-proposal.json'
OLD = ROOT/'runs/typed-composer-recovered-128-scorefix-v1'
OUT = ROOT/'runs/typed-semantic-fresh-fit-128-v1'
ARMS = ('raw','structural_control','literal_candidate','semantic_candidate','nearest_training_graph')
load = lambda p:json.loads(p.read_text())
read_rows = lambda p:[json.loads(s) for s in p.read_text().splitlines() if s.strip()]


def main():
    if OUT.exists():raise ValueError('New run only; preserve any previous attempt')
    proposal=load(PROPOSAL)
    for name,h in proposal['assets_sha256'].items():assert sha(ROOT/name)==h,name
    assert sha(EMBEDDING_DIR/'model.safetensors')==proposal['encoder']['model_sha256']
    assert sha(EMBEDDING_DIR/'tokenizer.json')==proposal['encoder']['tokenizer_sha256']
    identity=typed_codec.frozen(ROOT/'contracts/typed_codec_v1.json')
    pairs=typed_confirmation.verify_development(ROOT/'runs/typed-real-dev-v5/pairs.jsonl',ROOT/'findings/typed-real-dev-v5/summary.json',identity)
    fit=[p for p in pairs if p['learning_split']=='development_fit']
    unique={}
    for p in fit:
        if p['uid'] in unique:assert p['input']==unique[p['uid']]['input']
        unique.setdefault(p['uid'],p)
    requests=list(unique.values())
    old_captures={c['uid']:c for c in read_rows(OLD/'captures.jsonl') if c['split']=='development_fit'}
    assert len(fit)==15 and len(requests)==10 and set(unique)==set(old_captures)
    config=load(OLD/'candidate.json')['config']
    structural=dict(config['correction'],include_interior_empty=True)
    literal=dict(pool_size=8,max_edits=2,max_executions=4,wall_seconds=.25)
    source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'algsolve').rglob('*.py'))}
    original_hashes={n:sha(OLD/n) for n in ['candidate.json','captures.jsonl','decisions.jsonl','scores.jsonl','summary.json']}
    manifest=dict(name=OUT.name,proposal_sha256=sha(PROPOSAL),proposal=proposal,structural_config=structural,literal_config=literal,
        arms=ARMS,source_sha256=source_hashes,driver_sha256=sha(Path(__file__)),original_sha256=original_hashes,
        dependencies={n:importlib.metadata.version(n) for n in ['torch','transformers','numpy']},python=sys.executable,
        encoder_files_sha256={n:sha(EMBEDDING_DIR/n) for n in ['config.json','tokenizer_config.json']},
        query_authority='Only public request/signature/examples reach decision routes. Expected identity, target graph and independent tests cannot select repairs.',
        fit_memory='15 original qualified fit graphs; same memory and similarities for model and nearest baseline; no target selected by query UID.',
        semantic='Two top non-current recipe logits per recipe slot, four ranked one-operation alternatives, typed validation then literal fallback; one shared four-execution and .25second budget. Candidate frozen before this run.',
        workload='Fleet reports both27Bcontributors gracefully stopped;0.8B and2Bremain. Existingload, not exclusive-host timing.',
        literals='One/two flips among8 lowest absolute literal logits; bool only unit magnitude bit; maximum4 extra public executions and0.25s within2s total.',
        timing='Fresh shared inference charged to each neural arm. Structural/first-public prefix shared between control and candidate and charged in full; literal wrapper and search measured additionally. Nearest excludes predictor time. Cold setup and independent scoring separate.',
        training=False,protected_opened=False,scoring_seal_required=True)
    OUT.mkdir();publish(OUT/'candidate.json',manifest)
    monitor=Monitor([OUT,EMBEDDING_DIR,ROOT/'runs/typed-student-v2',ROOT/'runs/typed-real-dev-v5'],seconds=300)
    monitor.start();run_start=time.perf_counter()
    try:
        torch.set_num_threads(4);torch.set_num_interop_threads(1)
        assert torch.equal(torch.ones((2,2))@torch.ones((2,2)),torch.full((2,2),2.))
        print('[run-contract] run_name='+OUT.name+' pairs_input_spec=original15-fit-graphs10-fit-queries resume_from=typed-student-v2 resume_stage=evaluation decode=parallel-plus-model-ranked-recipes-and-literal-bits eval_dataset_paths=consumed-fit-only device=cpu schedule=no-training runtime_mode=reviewed-linux-sandbox sweep_mode=none',flush=True)
        print(json.dumps(dict(python=sys.executable,torch=torch.__version__,cuda_available=torch.cuda.is_available(),cuda_count=torch.cuda.device_count(),device='cpu')),flush=True)
        tick=time.perf_counter();checkpoint=torch.load(ROOT/'runs/typed-student-v2/model.pt',map_location='cpu',weights_only=True)
        training=checkpoint['contract'];assert training['codec_sha256']==identity
        assert training['dataset_sha256']==proposal['assets_sha256']['runs/typed-real-dev-v5/pairs.jsonl']
        descriptor=training['prediction_encoding'];encoding=PredictionCodec(descriptor['slots'],descriptor['types'])
        assert encoding.descriptor()==descriptor
        model=TypedPredictor(checkpoint['state_dict']['project.weight'].shape[1],encoding.slots,len(encoding.types),width=training['width'])
        model.load_state_dict(checkpoint['state_dict'],strict=True);model.eval()
        setup={'checkpoint_load_seconds':time.perf_counter()-tick}
        problem=problem_for(requests[0])
        probe=validate.judge_problem(problem,'class Solution:\n    def '+problem.entry['method']+'(self,*args):\n        return 7\n',
                                     [{'args':[0 for _ in problem.params],'expected':7}],wall_seconds=5)
        publish(OUT/'sandbox_probe.json',probe.to_dict());assert probe.passed,probe
        tick=time.perf_counter();embedder=Embedder(device='cpu');setup['encoder_setup_seconds']=time.perf_counter()-tick
        descriptions=[typed_codec.digest(p['target'])+' '+json.dumps(p['target']['program'],sort_keys=True) for p in fit]
        tick=time.perf_counter();memory=embedder.encode(descriptions,batch_size=4);setup['fit_memory_embedding_seconds']=time.perf_counter()-tick
        tick=time.perf_counter();warm=embedder.encode(['Return an integer input unchanged.'],query=True,instruction=INSTRUCTION)[0]
        with torch.inference_mode():model(torch.from_numpy(warm[None]),torch.from_numpy(memory[:4][None]))
        setup['warmup_seconds']=time.perf_counter()-tick;publish(OUT/'setup.json',setup)
        captures=[]
        for i,pair in enumerate(requests):
            tick=time.perf_counter();vector=embedder.encode([query_text(pair)],query=True,instruction=INSTRUCTION)[0]
            embedding=time.perf_counter()-tick
            tick=time.perf_counter();similarities=memory@vector;neighbors=np.argsort(-similarities,kind='stable')[:4]
            retrieval=time.perf_counter()-tick;tick=time.perf_counter()
            with torch.inference_mode():
                logits=model(torch.from_numpy(vector[None]),torch.from_numpy(memory[neighbors][None]))
                raw=decisions(logits);scores={k:v[0].tolist() for k,v in logits.items()}
            prediction=time.perf_counter()-tick
            capture=dict(uid=pair['uid'],codes=raw,logits=scores,similarities=similarities.tolist(),
                         embedding_seconds=embedding,retrieval_seconds=retrieval,prediction_seconds=prediction,
                         historical_raw_match=raw==old_captures[pair['uid']]['codes'])
            publish(OUT/f'capture-{i:04d}.json',capture);captures.append(capture)
            print(json.dumps(dict(captured=i+1,raw_match=capture['historical_raw_match'])),flush=True)
        assert all(c['historical_raw_match'] for c in captures),'Raw parity failed; no repairs or scoring authorized'
        publish(OUT/'capture-seal.json',dict(captures_sha256={p.name:sha(p) for p in sorted(OUT.glob('capture-[0-9][0-9][0-9][0-9].json'))},raw_parity_cases=10))
        route_rows=[]
        for i,(pair,capture) in enumerate(zip(requests,captures)):
            problem=problem_for(pair);shared=sum(capture[k] for k in ['embedding_seconds','retrieval_seconds','prediction_seconds'])
            common=(problem,capture['codes'],capture['logits'],encoding,identity,shared,structural,2.)
            routes={'raw':run_route('raw',*common),'structural_control':run_route('constrained',*common)}
            routes['literal_candidate']=run_literal_route(routes['structural_control'],problem,capture['logits']['bits'],encoding,identity,literal,2.)
            routes['semantic_candidate']=run_semantic_route(routes['structural_control'],problem,capture['logits'],encoding,identity,literal,2.)
            tick=time.perf_counter();graph,h,reason=nearest_graph({'input':pair['input']},fit,capture['similarities'],encoding)
            build=time.perf_counter()-tick
            routes['nearest_training_graph']=run_route('nearest_training_graph',*common,baseline_graph=graph,baseline_hash=h,
                baseline_reason=reason,baseline_seconds=capture['embedding_seconds']+capture['retrieval_seconds'],baseline_construction_seconds=build)
            record=dict(uid=pair['uid'],split='development_fit',routes=routes)
            publish(OUT/f'decision-{i:04d}.json',record);route_rows.append(record)
            print(json.dumps(dict(uid=pair['uid'],decisions={a:r['decision'] for a,r in routes.items()},literal_executions=(routes['literal_candidate'].get('literal_repair') or {}).get('executions',0))),flush=True)
        publish(OUT/'decisions-seal.json',dict(candidate_sha256=sha(OUT/'candidate.json'),capture_seal_sha256=sha(OUT/'capture-seal.json'),
            decisions_sha256={p.name:sha(p) for p in sorted(OUT.glob('decision-[0-9][0-9][0-9][0-9].json'))}))
        scored=[]
        for i,(pair,row) in enumerate(zip(requests,route_rows)):
            problem=problem_for(pair);tests,_=development_tests.select(pair['uid'],load_hidden_tests(problem))
            assert mine.digest(tests)==pair['provenance']['independent_tests_sha256']
            score=dict(uid=pair['uid'],routes={a:score_fixed(r,problem,tests) for a,r in row['routes'].items()})
            publish(OUT/f'score-{i:04d}.json',score);scored.append(score)
        metrics={}
        for arm in ARMS:
            values=[r['routes'][arm] for r in scored];times=[r['timing']['total_seconds'] for r in values]
            metrics[arm]=dict(cases=10,valid=sum(r['structurally_valid'] for r in values),accepted_correct=sum(r['accepted_correct'] for r in values),
                wrong_acceptances=sum(r['wrong_acceptance'] for r in values),abstentions=sum(r['decision']=='abstain' for r in values),
                infrastructure_failures=sum(r['infrastructure_failure'] for r in values),
                latency_seconds=dict(p50=float(np.percentile(times,50)),p95=float(np.percentile(times,95)),maximum=max(times)),
                literal_seconds=sum(r['timing'].get('literal_seconds',0)+r['timing'].get('semantic_seconds',0) for r in values),
                extra_public_executions=sum((r.get('semantic_repair') or r.get('literal_repair') or {}).get('executions',0) for r in values))
        useful=[r['uid'] for r in scored if r['routes']['semantic_candidate']['accepted_correct'] and not r['routes']['structural_control']['accepted_correct']]
        harmful=[r['uid'] for r in scored if r['routes']['structural_control']['accepted_correct'] and not r['routes']['semantic_candidate']['accepted_correct']]
        m=metrics['semantic_candidate'];accepted=bool(useful and not harmful and not m['wrong_acceptances'] and not any(v['infrastructure_failures'] for v in metrics.values()) and m['latency_seconds']['p95']<=2.)
        compact=[]
        for r in scored:
            compact.append(dict(uid=r['uid'],routes={a:dict(decision=v['decision'],reason=v['reason'],correct=v['accepted_correct'],wrong=v['wrong_acceptance'],
                valid=v['structurally_valid'],timing=v['timing'],literal_repair={k:value for k,value in (v.get('semantic_repair') or v.get('literal_repair') or {}).items() if k not in ['final_codes','attempts']},
                attempt_summary=[dict(edits=t['edits'],validation_failure=t['validation_failure'],public_passed=(t['public'] or {}).get('passed'),public_reason=(t['public'] or {}).get('reason'),execution_seconds=t['execution_seconds']) for t in (v.get('semantic_repair') or v.get('literal_repair') or {}).get('attempts',[])]) for a,v in r['routes'].items()}))
        summary=dict(name=OUT.name,candidate_sha256=sha(OUT/'candidate.json'),metrics=metrics,useful=useful,harmful=harmful,
            fit_development_signal=accepted,release_qualified=False,protected_opened=False,rows=compact,setup=setup,resources=monitor.counters(),
            actual_wall_seconds=time.perf_counter()-run_start,raw_parity_cases=10,
            limitations=['Consumed fit only; no fresh generalization','Historical encoding/truncation retained for matched inference','Phase-charged full routes share inference and control prefix; actual run wall and setup separate','Existing Reploid load; no exclusive-host timing claim'])
        assert original_hashes=={n:sha(OLD/n) for n in original_hashes},'Historical evidence changed'
        assert source_hashes=={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'algsolve').rglob('*.py'))},'Source drift'
        publish(OUT/'summary.json',summary)
        print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2),flush=True)
    except BaseException as error:
        publish(OUT/'failure.json',dict(error=type(error).__name__,detail=str(error),resources=monitor.counters()))
        raise
    finally:monitor.stop.set()


if __name__=='__main__':main()
