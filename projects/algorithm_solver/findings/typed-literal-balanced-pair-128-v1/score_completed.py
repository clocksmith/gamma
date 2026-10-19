"""Exactly the owner-approved two-arm original-corpus experiment; no retries."""
import gc, hashlib, importlib.metadata, json, os, sys, time
from pathlib import Path
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer
from algsolve import validate
from algsolve.embed import EMBEDDING_DIR, verify_weights
from algsolve.records import LANE_ROOT as ROOT, load_hidden_tests
from algsolve.rebuild_recognition import Monitor, sha, publish
from algsolve.synth import typed_codec, typed_confirmation, development_tests, mine
from algsolve.synth.train_typed import query_text, problem_for, INSTRUCTION
from algsolve.synth.typed_prediction_codec import PredictionCodec
from algsolve.synth.typed_predictor import TypedPredictor, decisions, per_example_loss
from algsolve.synth.typed_balanced_loss import per_example_balanced_loss
from algsolve.synth.typed_comparison import run_route, nearest_graph, score_fixed
from algsolve.synth.typed_semantic_repair import run_semantic_route
from algsolve.synth.typed_guard_filter import unreachable_numeric_guard
NAME='typed-literal-balanced-pair-128-v1-scoring'
PRIOR=ROOT/'runs/typed-literal-balanced-pair-128-v1'
OUT=ROOT/'runs'/NAME
PACKET=ROOT/'findings/typed-literal-objective-proposal-128-v1/owner-approval-packet.json'
load=lambda p:json.loads(p.read_text())

def main():
    assert not OUT.exists(),'Preserve scoring evidence'
    frozen=load(PRIOR/'contract.json');packet=load(PACKET)
    assert sha(PACKET)==frozen['packet_sha256'] and load(PRIOR/'failure.json')['detail']=='Frozen artifact differs: setup.json'
    assert not list(PRIOR.glob('decision-*.json')) and not list(PRIOR.glob('score-*.json'))
    assert all(sha(ROOT/n)==h for n,h in frozen['sources_sha256'].items())
    identity=typed_codec.frozen(ROOT/'contracts/typed_codec_v1.json');path=ROOT/packet['original']['corpus']
    pairs=typed_confirmation.verify_development(path,ROOT/'findings/typed-real-dev-v5/summary.json',identity)
    fit=[p for p in pairs if p['learning_split']=='development_fit'];unique={}
    for p in fit:unique.setdefault(p['uid'],p)
    encoding=PredictionCodec.fit(fit);structural=frozen['structural'];literal=frozen['literal'];models={'control':None,'balanced':None}
    checkpoints=load(PRIOR/'checkpoints-seal.json')
    for arm,h in checkpoints.items():assert sha(PRIOR/arm/'model.pt')==h and load(PRIOR/arm/'training.json')['steps']==400
    captures=[load(PRIOR/f'capture-{arm}-{i:02d}.json') for arm in models for i in range(10)]
    assert len(captures)==20 and all(c['uid'] in unique for c in captures)
    OUT.mkdir();publish(OUT/'contract.json',dict(name=NAME,mode='Scoring-only continuation after receipt-write failure; no new optimizer steps, encoder or query inference',prior_contract_sha256=sha(PRIOR/'contract.json'),failure_sha256=sha(PRIOR/'failure.json'),driver_sha256=sha(Path(__file__)),captures_sha256={p.name:sha(p) for p in PRIOR.glob('capture-*.json')},checkpoints_sha256=checkpoints,remaining_combined_wall_seconds=2200,query_timing='Actual preserved fresh-query timings charged in full; not a query cache speed claim',missing_setup_timing='Second encoder-load and warmup timings were not committed before failure; do not invent them',protected_opened=False,audit_opened=False))
    monitor=Monitor([OUT,PRIOR,EMBEDDING_DIR,ROOT/'runs/typed-real-dev-v5',ROOT/'runs/typed-student-v2'],seconds=2200);monitor.start();os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);torch.set_num_threads(2);start=time.perf_counter()
    try:
        rows=[]
        for i,c in enumerate(captures):
            pair=unique[c['uid']];problem=problem_for(pair);shared=sum(c[k] for k in ('embedding_seconds','retrieval_seconds','prediction_seconds'));common=(problem,c['codes'],c['logits'],encoding,identity,shared,structural,2.)
            raw=run_route('raw',*common);fixed=run_route('constrained',*common);guard=run_semantic_route(fixed,problem,c['logits'],encoding,identity,literal,2.,literal_filter=unreachable_numeric_guard)
            tick=time.perf_counter();graph,h,reason=nearest_graph({'input':pair['input']},fit,c['similarities'],encoding);build=time.perf_counter()-tick
            nearest=run_route('nearest_training_graph',*common,baseline_graph=graph,baseline_hash=h,baseline_reason=reason,baseline_seconds=c['embedding_seconds']+c['retrieval_seconds'],baseline_construction_seconds=build)
            row=dict(arm=c['arm'],uid=c['uid'],routes=dict(raw=raw,guard=guard,nearest=nearest));rows.append(row);publish(OUT/f'decision-{i:02d}.json',row)
        publish(OUT/'decisions-seal.json',{p.name:sha(p) for p in OUT.glob('decision-*.json')})
        scored=[]
        for i,row in enumerate(rows):
            pair=unique[row['uid']];problem=problem_for(pair);tests,_=development_tests.select(pair['uid'],load_hidden_tests(problem));assert mine.digest(tests)==pair['provenance']['independent_tests_sha256']
            score=dict(arm=row['arm'],uid=row['uid'],routes={a:score_fixed(r,problem,tests) for a,r in row['routes'].items()});scored.append(score);publish(OUT/f'score-{i:02d}.json',score)
        metrics={};by={}
        for arm in models:
            by[arm]={r['uid']:r for r in scored if r['arm']==arm};metrics[arm]={}
            for route in ('raw','guard','nearest'):
                rs=[r['routes'][route] for r in by[arm].values()];times=[r['timing']['total_seconds'] for r in rs]
                metrics[arm][route]=dict(cases=10,correct=sum(r['accepted_correct'] for r in rs),independently_correct=sum(r['independently_correct'] is True for r in rs),wrong=sum(r['wrong_acceptance'] for r in rs),infrastructure=sum(r['infrastructure_failure'] for r in rs),p95=float(np.percentile(times,95)),abstentions=sum(r['decision']=='abstain' for r in rs))
        literal_diagnostics=[]
        for capture in captures:
            alternatives=[]
            for pair in fit:
                if pair['uid']!=capture['uid']:continue
                target=np.asarray(encoding.encode(pair['target']['program'])['bits']);pred=np.asarray(capture['codes']['bits']);mask=target!=-100
                active=mask.any(axis=1);exact=((target==pred)|~mask).all(axis=1)
                alternatives.append(dict(graph_sha256=pair['graph_sha256'],supervised_bits=int(mask.sum()),wrong_bits=int(((target!=pred)&mask).sum()),supervised_literals=int(active.sum()),whole_literals_correct=int((exact&active).sum()),whole_literal_vector_correct=bool(exact.all())))
            literal_diagnostics.append(dict(arm=capture['arm'],uid=capture['uid'],alternatives=alternatives,any_qualified_alternative_literal_vector_correct=any(a['whole_literal_vector_correct'] for a in alternatives)))
        publish(OUT/'literal-diagnostics.json',literal_diagnostics)
        losses={r:[uid for uid in unique if by['control'][uid]['routes'][r]['accepted_correct'] and not by['balanced'][uid]['routes'][r]['accepted_correct']] for r in ('raw','guard')}
        quality=all(metrics['balanced'][r]['correct']>=metrics['control'][r]['correct']+1 and not losses[r] for r in ('raw','guard')) and not any(v['wrong'] or v['infrastructure'] for m in metrics.values() for v in m.values())
        assert all(sha(ROOT/n)==h for n,h in frozen['sources_sha256'].items()) and all(sha(Path(n))==h for n,h in judge_frozen['sources_sha256'].items()),'Frozen implementation changed'
        assert sha(PACKET)==frozen['packet_sha256'] and sha(path)==packet['original']['corpus_sha256']
        summary=dict(name=NAME,checkpoints_sha256=checkpoints,metrics=metrics,lost_correct=losses,quality_pass=quality,latency_pass=metrics['balanced']['guard']['p95']<=2,release_qualified=False,protected_opened=False,audit_opened=False,resources=monitor.counters(),actual_wall_seconds=time.perf_counter()-start)
        publish(OUT/'summary.json',summary);print('[summary] '+json.dumps(summary),flush=True)
    except BaseException as e:
        publish(OUT/'failure.json',dict(error=type(e).__name__,detail=str(e),resources=monitor.counters()));raise
    finally:monitor.stop.set()
if __name__=='__main__':main()
