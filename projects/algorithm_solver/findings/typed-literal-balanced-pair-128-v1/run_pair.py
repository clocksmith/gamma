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
NAME='typed-literal-balanced-pair-128-v1'
OUT=ROOT/'runs'/NAME
PACKET=ROOT/'findings/typed-literal-objective-proposal-128-v1/owner-approval-packet.json'
load=lambda p:json.loads(p.read_text())

def tensor_identity(model):
    tensors={k:dict(dtype=str(v.dtype),shape=list(v.shape),sha256=hashlib.sha256(v.detach().cpu().contiguous().numpy().tobytes()).hexdigest()) for k,v in sorted(model.state_dict().items())}
    return hashlib.sha256(json.dumps(tensors,sort_keys=True,separators=(',',':')).encode()).hexdigest()

class FullEncoder:
    def __init__(self):
        self.tokenizer=AutoTokenizer.from_pretrained(EMBEDDING_DIR,padding_side='left',local_files_only=True)
        self.model=AutoModel.from_pretrained(EMBEDDING_DIR,dtype=torch.float32,local_files_only=True).to('cpu').eval()
    def encode(self,texts):
        vectors=[]
        for text in texts:
            tokens=self.tokenizer([text],padding=True,truncation=False,return_tensors='pt')
            assert tokens['input_ids'].shape[1]<=2048,'No truncation or input omission allowed'
            with torch.inference_mode():
                hidden=self.model(**tokens).last_hidden_state
                vector=torch.nn.functional.normalize(hidden[:,-1].float(),dim=-1).cpu().numpy()[0]
            assert np.isfinite(vector).all();vectors.append(vector)
        return np.array(vectors)

def main():
    assert not OUT.exists(),'Preserve prior attempt; no automatic retry'
    packet=load(PACKET);identity=typed_codec.frozen(ROOT/'contracts/typed_codec_v1.json')
    assert identity==packet['original']['codec_sha256']
    path=ROOT/packet['original']['corpus'];assert sha(path)==packet['original']['corpus_sha256']
    assert sha(ROOT/packet['original']['checkpoint'])==packet['original']['checkpoint_sha256']
    verify_weights()
    for name,h in packet['shared_configuration']['encoder_files_sha256'].items():assert sha(EMBEDDING_DIR/name)==h
    for arm,source in [('control','typed_predictor.py'),('candidate','typed_balanced_loss.py')]:assert sha(ROOT/'algsolve/synth'/source)==packet[arm]['loss_source_sha256']
    pairs=typed_confirmation.verify_development(path,ROOT/'findings/typed-real-dev-v5/summary.json',identity)
    fit=[p for p in pairs if p['learning_split']=='development_fit'];unique={}
    for p in fit:
        if p['uid'] in unique:assert p['input']==unique[p['uid']]['input']
        unique.setdefault(p['uid'],p)
    requests=list(unique.values());assert len(fit)==15 and len(requests)==10
    assert set(p['problem_family'] for p in fit)==set(packet['family_separation']['fit_families'])
    original=torch.load(ROOT/packet['original']['checkpoint'],map_location='cpu',weights_only=True)
    descriptor=original['contract']['prediction_encoding'];encoding=PredictionCodec(descriptor['slots'],descriptor['types'])
    assert encoding.descriptor()==PredictionCodec.fit(fit).descriptor()==descriptor
    torch.set_num_threads(4);torch.set_num_interop_threads(1);torch.manual_seed(17)
    initial=TypedPredictor(1024,encoding.slots,len(encoding.types))
    assert tensor_identity(initial)==packet['control']['initial_tensor_manifest_sha256'];del initial,original
    labels={k:torch.tensor([encoding.encode(p['target']['program'])[k] for p in fit]) for k in encoding.encode(fit[0]['target']['program'])}
    indices={p['uid']:i for i,p in enumerate(requests)};fit_indices=[indices[p['uid']] for p in fit]
    groups=[[j for j,p in enumerate(fit) if p['uid']==uid] for uid in unique]
    descriptions=[typed_codec.digest(p['target'])+' '+json.dumps(p['target']['program'],sort_keys=True) for p in fit]
    texts=[INSTRUCTION+query_text(p) for p in requests]
    tokenizer=AutoTokenizer.from_pretrained(EMBEDDING_DIR,local_files_only=True)
    counts=[len(tokenizer(t,truncation=False)['input_ids']) for t in descriptions+texts];assert max(counts)==1660 and max(counts)<=2048
    old=load(ROOT/'findings/typed-gpu-reuse-fit-128-v2/contract.json');structural=old['structural'];literal=old['literal']
    sources={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'algsolve').rglob('*.py')) if not p.name.startswith('dependency_')}
    # Judge implementation is outside the lane and must remain fixed as well.
    judge_sources={str(p):sha(p) for p in sorted((ROOT.parents[1]/'src').rglob('*judge*.py'))}
    contract=dict(name=NAME,owner_authorized=True,authorization='User: i approve ... finish it all; scoped prior owner packet',packet_sha256=sha(PACKET),driver_sha256=sha(Path(__file__)),packet=packet,sources_sha256=sources,judge_sources_sha256=judge_sources,token_counts=counts,structural=structural,literal=literal,audit_opened=False,protected_opened=False)
    OUT.mkdir();publish(OUT/'contract.json',contract)
    monitor=Monitor([OUT,EMBEDDING_DIR,ROOT/'runs/typed-real-dev-v5',ROOT/'runs/typed-student-v2'],seconds=2400);monitor.start();start=time.perf_counter()
    try:
        assert torch.equal(torch.ones(2,2)@torch.ones(2,2),torch.full((2,2),2.))
        runtime=dict(python=sys.executable,versions={n:importlib.metadata.version(n) for n in ('torch','transformers','numpy')},cuda_available=torch.cuda.is_available(),cuda_count=torch.cuda.device_count(),target='cpu',cpu_matmul='passed',gpu_jobs=0)
        publish(OUT/'runtime.json',runtime);print('[compute] '+json.dumps(runtime),flush=True)
        print(f'[run-contract] run_name={NAME} pairs_input_spec={path} resume_from=none resume_stage=none decode=parallel-argmax eval_dataset_paths=consumed-fit-only device=cpu schedule=control_then_balanced runtime_mode=cpu sweep_mode=after_train',flush=True)
        problem=problem_for(requests[0]);probe=validate.judge_problem(problem,'class Solution:\n    def '+problem.entry['method']+'(self,*args):\n        return 7\n',[{'args':[0 for _ in problem.params],'expected':7}],wall_seconds=5)
        publish(OUT/'sandbox_probe.json',probe.to_dict());assert probe.passed
        tick=time.perf_counter();encoder=FullEncoder();setup={'load_seconds':time.perf_counter()-tick}
        tick=time.perf_counter();memory=encoder.encode(descriptions);vectors=encoder.encode(texts);setup['training_embedding_seconds']=time.perf_counter()-tick
        np.savez(OUT/'training-vectors.npz',memory=memory,queries=vectors)
        del encoder;gc.collect()
        # Release model allocations before predictor optimization, not just references.
        import ctypes
        ctypes.CDLL(None).malloc_trim(0)
        setup['encoder_released_before_optimizer']=True;publish(OUT/'setup.json',setup)
        neighbors=np.array([np.argsort(-(memory@v),kind='stable')[:4] for v in vectors])
        query=torch.from_numpy(vectors);retrieval=torch.from_numpy(memory[neighbors]);models={};checkpoints={}
        for arm,loss_fn in [('control',per_example_loss),('balanced',per_example_balanced_loss)]:
            folder=OUT/arm;folder.mkdir();torch.manual_seed(17)
            model=TypedPredictor(1024,encoding.slots,len(encoding.types));assert tensor_identity(model)==packet['control']['initial_tensor_manifest_sha256']
            optimizer=torch.optim.AdamW(model.parameters(),lr=.001);model.train();tick=time.perf_counter()
            with (folder/'metrics.jsonl').open('x') as stream:
                for step in range(400):
                    assert time.perf_counter()-tick<900,'Per-arm 900-second training budget exceeded'
                    optimizer.zero_grad();logits=model(query[fit_indices],retrieval[fit_indices]);per_target=loss_fn(logits,labels)
                    loss=torch.stack([per_target[g].min() for g in groups]).mean();assert torch.isfinite(loss)
                    loss.backward();optimizer.step()
                    if step==0 or (step+1)%20==0:
                        row=dict(arm=arm,step=step+1,loss=float(loss.detach()),seconds=time.perf_counter()-tick);stream.write(json.dumps(row)+'\n');stream.flush();print('[train] '+json.dumps(row),flush=True)
            assert time.perf_counter()-tick<=900
            trained_contract=dict(codec_sha256=identity,dataset_sha256=sha(path),prediction_encoding=descriptor,width=64,steps=400,seed=17,context_tokens=2048,loss=arm,experiment_contract_sha256=sha(OUT/'contract.json'))
            torch.save(dict(state_dict=model.state_dict(),contract=trained_contract),folder/'model.pt');checkpoints[arm]=sha(folder/'model.pt');models[arm]=model.eval()
            publish(folder/'training.json',dict(steps=400,seconds=time.perf_counter()-tick,checkpoint_sha256=checkpoints[arm]));del optimizer,logits,per_target,loss;gc.collect()
        publish(OUT/'checkpoints-seal.json',checkpoints)
        tick=time.perf_counter();encoder=FullEncoder();setup['evaluation_encoder_load_seconds']=time.perf_counter()-tick
        encoder.encode(['Return an integer input unchanged.']);captures=[]
        for arm,model in models.items():
            for i,pair in enumerate(requests):
                tick=time.perf_counter();vector=encoder.encode([INSTRUCTION+query_text(pair)])[0];embedding=time.perf_counter()-tick
                tick=time.perf_counter();similarities=memory@vector;near=np.argsort(-similarities,kind='stable')[:4];retrieval_time=time.perf_counter()-tick
                tick=time.perf_counter()
                with torch.inference_mode():logits=model(torch.from_numpy(vector[None]),torch.from_numpy(memory[near][None]));raw=decisions(logits);scores={k:v[0].tolist() for k,v in logits.items()}
                row=dict(arm=arm,uid=pair['uid'],codes=raw,logits=scores,similarities=similarities.tolist(),neighbors=near.tolist(),vector=vector.tolist(),embedding_seconds=embedding,retrieval_seconds=retrieval_time,prediction_seconds=time.perf_counter()-tick)
                publish(OUT/f'capture-{arm}-{i:02d}.json',row);captures.append(row);print('[capture] '+json.dumps(dict(arm=arm,uid=pair['uid'],embedding_seconds=embedding)),flush=True)
        del encoder;gc.collect();ctypes.CDLL(None).malloc_trim(0)
        publish(OUT/'setup.json',setup);publish(OUT/'captures-seal.json',{p.name:sha(p) for p in OUT.glob('capture-*.json')})
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
        assert all(sha(ROOT/n)==h for n,h in sources.items()) and all(sha(Path(n))==h for n,h in judge_sources.items()),'Frozen implementation changed'
        assert sha(PACKET)==contract['packet_sha256'] and sha(path)==packet['original']['corpus_sha256']
        summary=dict(name=NAME,checkpoints_sha256=checkpoints,metrics=metrics,lost_correct=losses,quality_pass=quality,latency_pass=metrics['balanced']['guard']['p95']<=2,release_qualified=False,protected_opened=False,audit_opened=False,resources=monitor.counters(),actual_wall_seconds=time.perf_counter()-start)
        publish(OUT/'summary.json',summary);print('[summary] '+json.dumps(summary),flush=True)
    except BaseException as e:
        publish(OUT/'failure.json',dict(error=type(e).__name__,detail=str(e),resources=monitor.counters()));raise
    finally:monitor.stop.set()
if __name__=='__main__':main()
