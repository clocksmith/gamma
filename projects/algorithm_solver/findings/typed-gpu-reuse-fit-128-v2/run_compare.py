"""Paired existing CPU/GPU encoder evaluation; no training or query cache."""
import gc
import importlib.metadata
import json
import os
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
from algsolve.synth.typed_semantic_repair import run_semantic_route
from algsolve.synth.typed_guard_filter import unreachable_numeric_guard

OUT=ROOT/'runs/typed-gpu-reuse-fit-128-v2'
PRIOR=ROOT/'runs/typed-gpu-reuse-fit-128-v1'
OLD=ROOT/'runs/typed-composer-recovered-128-scorefix-v1'
PROPOSAL=ROOT/'findings/typed-fit-semantic-diagnosis-128-v1/literal-construction-proposal.json'
DEVICES=('cpu','cuda')
ARMS=('raw','structural_control','guard_candidate','nearest_training_graph')
load=lambda p:json.loads(p.read_text())

def main():
    assert not OUT.exists(),'Preserve previous run'
    proposal=load(PROPOSAL)
    for name,h in proposal['assets_sha256'].items():assert sha(ROOT/name)==h,name
    for name in ('model','tokenizer'):
        filename='model.safetensors' if name=='model' else 'tokenizer.json'
        assert sha(EMBEDDING_DIR/filename)==proposal['encoder'][name+'_sha256']
    identity=typed_codec.frozen(ROOT/'contracts/typed_codec_v1.json')
    pairs=typed_confirmation.verify_development(ROOT/'runs/typed-real-dev-v5/pairs.jsonl',ROOT/'findings/typed-real-dev-v5/summary.json',identity)
    fit=[p for p in pairs if p['learning_split']=='development_fit']
    unique={}
    for p in fit:
        if p['uid'] in unique:assert p['input']==unique[p['uid']]['input']
        unique.setdefault(p['uid'],p)
    requests=list(unique.values())
    old={c['uid']:c for c in [json.loads(s) for s in (OLD/'captures.jsonl').read_text().splitlines()] if c['split']=='development_fit'}
    assert len(fit)==15 and len(requests)==10 and set(unique)==set(old)
    structural=dict(load(OLD/'candidate.json')['config']['correction'],include_interior_empty=True)
    literal=dict(pool_size=8,max_edits=2,max_executions=4,wall_seconds=.25)
    excluded={'answer.py','approved_library.py','catalog_refresh.py','public_contracts.py'}
    sources={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'algsolve').rglob('*.py')) if p.name not in excluded}
    prior_captures=[load(PRIOR/f'capture-cpu-{i:04d}.json') for i in range(10)]
    assert all(r['historical_raw_match'] for r in prior_captures)
    assert load(PRIOR/'contract.json')['sources_sha256']==sources
    contract=dict(name=OUT.name,prior_failed_run='typed-gpu-reuse-fit-128-v1',prior_cpu_captures_sha256={f'capture-cpu-{i:04d}.json':sha(PRIOR/f'capture-cpu-{i:04d}.json') for i in range(10)},prior_contract_sha256=sha(PRIOR/'contract.json'),prior_cpu_setup_sha256=sha(PRIOR/'setup.json'),reuse='Reuse complete actual CPU inference captures from resource-rejected combined process; no decisions/scoring occurred. Fresh GPU-only process avoids retained CPU allocator. CPU timing remains actual original inference; no query cache or current CPU timing claim.',assets_sha256=proposal['assets_sha256'],encoder=proposal['encoder'],
        codec_sha256=identity,driver_sha256=sha(Path(__file__)),sources_sha256=sources,
        source_scope='All algsolve Python except concurrent recognition-only answer/approved_library/catalog_refresh/public_contracts; no composition dependency excluded.',
        dependencies={n:importlib.metadata.version(n) for n in ('torch','transformers','numpy')},python=sys.executable,
        devices=list(DEVICES),encoder_dtypes={'cpu':'float32','cuda':'float16'},predictor_device='cpu',predictor_dtype='float32',
        historical_gpu_route='findings/corpus-answer-gpu-v2: same encoder, standard Embedder GPU fp16, same Radeon8060S/ROCm7.2 runtime; composition requires this separate comparison',
        limits=dict(cpu_threads=2,root_rss_limit_bytes=6*1024**3,concurrent_catalog_limit_bytes=2*1024**3,aggregate_limit_bytes=8*1024**3,wall_seconds=300,run_asset_disk_bytes=5*1024**3),
        structural=structural,literal=literal,arms=list(ARMS),training=False,protected_opened=False,
        hypotheses='Existing GPU route may remove embedding deadline losses; measure vector/neighbor/raw/decision parity, never assume precision equivalence. No repair configuration changes.',
        scoring='Both device arms all public decisions sealed before any independent scoring. Ten consumed fit requests only; independent source tests hash-bound.',
        timing='Each query freshly embedded once per device. GPU encode returns host vector and synchronizes before timer stops. Shared inference and public-control prefix charged in full per arm. Cold setup/fit memory/warmup/independent scoring separate. Sequential CPU thenGPU; no causal device-only attribution under ongoing workload.',
        input_truncation='Retain original1024token evaluation representation including original long-fit truncation for matched historical inference only. Does not authorize new training.',
        policy='No query cache, downloads, dependency installation, model/codec changes, new training, public binding variant, audit/protected scoring or services changes.',
        acceptance='Development-only GPU reuse: >= CPUguard correct, zero wrong/harmful/infrastructure outcomes and GPUguard p95<=2sec. Numerical differences remain reported even if this passes; no release/protected qualification.')
    OUT.mkdir();publish(OUT/'contract.json',contract)
    monitor=Monitor([OUT,EMBEDDING_DIR,ROOT/'runs/typed-student-v2',ROOT/'runs/typed-real-dev-v5'],seconds=300)
    monitor.start();os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
    start=time.perf_counter()
    try:
        torch.set_num_threads(2);torch.set_num_interop_threads(1)
        a=torch.ones((2,2),device='cuda');b=a@a;torch.cuda.synchronize();assert b.cpu().tolist()==[[2.,2.],[2.,2.]]
        runtime=dict(torch=torch.__version__,cuda_available=torch.cuda.is_available(),cuda_count=torch.cuda.device_count(),device=torch.cuda.get_device_name(0),HSA_OVERRIDE_GFX_VERSION=os.getenv('HSA_OVERRIDE_GFX_VERSION'),tiny_matmul='passed')
        publish(OUT/'runtime.json',runtime)
        print('[run-contract] run_name='+OUT.name+' pairs_input_spec=original15-fit-graphs10-fit-queries resume_from=typed-student-v2 resume_stage=evaluation decode=parallel-plus-frozen-guard-repair eval_dataset_paths=consumed-fit-only device=cpu,cuda schedule=no-training runtime_mode=normal_rocm sweep_mode=none',flush=True)
        checkpoint=torch.load(ROOT/'runs/typed-student-v2/model.pt',map_location='cpu',weights_only=True)
        trained=checkpoint['contract'];assert trained['codec_sha256']==identity
        assert trained['dataset_sha256']==proposal['assets_sha256']['runs/typed-real-dev-v5/pairs.jsonl']
        descriptor=trained['prediction_encoding'];encoding=PredictionCodec(descriptor['slots'],descriptor['types']);assert encoding.descriptor()==descriptor
        model=TypedPredictor(checkpoint['state_dict']['project.weight'].shape[1],encoding.slots,len(encoding.types),width=trained['width']);model.load_state_dict(checkpoint['state_dict'],strict=True);model.eval()
        problem=problem_for(requests[0])
        probe=validate.judge_problem(problem,'class Solution:\n    def '+problem.entry['method']+'(self,*args):\n        return 7\n',[{'args':[0 for _ in problem.params],'expected':7}],wall_seconds=5)
        publish(OUT/'sandbox_probe.json',probe.to_dict());assert probe.passed,probe
        captures={'cpu':prior_captures};setups={'cpu':load(PRIOR/'setup.json')['cpu']};memories={}
        for i,row in enumerate(prior_captures):publish(OUT/f'capture-cpu-{i:04d}.json',row)
        descriptions=[typed_codec.digest(p['target'])+' '+json.dumps(p['target']['program'],sort_keys=True) for p in fit]
        for device in ('cuda',):
            torch.cuda.reset_peak_memory_stats()
            tick=time.perf_counter();embedder=Embedder(device=device);setup=dict(encoder_setup_seconds=time.perf_counter()-tick)
            tick=time.perf_counter();memory=embedder.encode(descriptions,batch_size=4);setup['fit_memory_embedding_seconds']=time.perf_counter()-tick;memories[device]=memory
            tick=time.perf_counter();warm=embedder.encode(['Return an integer input unchanged.'],query=True,instruction=INSTRUCTION)[0]
            with torch.inference_mode():model(torch.from_numpy(warm[None]),torch.from_numpy(memory[:4][None]))
            setup['warmup_seconds']=time.perf_counter()-tick
            rows=[]
            for i,pair in enumerate(requests):
                tick=time.perf_counter();vector=embedder.encode([query_text(pair)],query=True,instruction=INSTRUCTION)[0]
                if device=='cuda':torch.cuda.synchronize()
                embedding=time.perf_counter()-tick
                assert np.isfinite(vector).all() and np.isfinite(memory).all()
                tick=time.perf_counter();similarities=memory@vector;neighbors=np.argsort(-similarities,kind='stable')[:4];retrieval=time.perf_counter()-tick
                tick=time.perf_counter()
                with torch.inference_mode():
                    logits=model(torch.from_numpy(vector[None]),torch.from_numpy(memory[neighbors][None]));raw=decisions(logits);scores={k:v[0].tolist() for k,v in logits.items()}
                prediction=time.perf_counter()-tick
                row=dict(uid=pair['uid'],codes=raw,logits=scores,similarities=similarities.tolist(),neighbors=neighbors.tolist(),vector=vector.tolist(),embedding_seconds=embedding,retrieval_seconds=retrieval,prediction_seconds=prediction,historical_raw_match=raw==old[pair['uid']]['codes'])
                publish(OUT/f'capture-{device}-{i:04d}.json',row);rows.append(row)
                print(json.dumps(dict(device=device,captured=i+1,embedding_seconds=embedding,historical_raw_match=row['historical_raw_match'])),flush=True)
            setup['gpu_peak_allocated_bytes']=torch.cuda.max_memory_allocated();setup['gpu_peak_reserved_bytes']=torch.cuda.max_memory_reserved()
            current_rss=int(next(s.split()[1] for s in Path('/proc/self/status').read_text().splitlines() if s.startswith('VmRSS:')))*1024
            setup['process_rss_after_capture_bytes']=current_rss
            setups[device]=setup;publish(OUT/'setup.json',setups)
            # GPU accounting is separate from cgroup host RSS; conservative combined endpoint cap.
            assert current_rss+setup['gpu_peak_reserved_bytes']<6*1024**3,'Combined process RSS + GPU peak reservation exceeds root6GiB'
            setups[device]=setup;captures[device]=rows;publish(OUT/'setup.json',setups)
            if device=='cpu':assert all(r['historical_raw_match'] for r in rows),'CPU historical parity drift; stop'
            del embedder;gc.collect();torch.cuda.empty_cache()
        parity=dict(memory_vectors_comparison='Unavailable: original failed run retained per-query similarities, not memory vectors; report query vector and neighbor differences only.',rows=[])
        for a,b in zip(captures['cpu'],captures['cuda']):
            parity['rows'].append(dict(uid=a['uid'],vector_max_abs=float(np.max(np.abs(np.array(a['vector'])-b['vector']))),cosine=float(np.dot(a['vector'],b['vector'])),neighbors_equal=a['neighbors']==b['neighbors'],raw_equal=a['codes']==b['codes'],changed_heads=[k for k in a['codes'] if a['codes'][k]!=b['codes'][k]]))
        publish(OUT/'parity.json',parity)
        publish(OUT/'capture-seal.json',dict(captures_sha256={p.name:sha(p) for p in sorted(OUT.glob('capture-*-????.json'))},parity_sha256=sha(OUT/'parity.json')))
        rows=[]
        for device in DEVICES:
            for i,(pair,capture) in enumerate(zip(requests,captures[device])):
                problem=problem_for(pair);shared=sum(capture[k] for k in ('embedding_seconds','retrieval_seconds','prediction_seconds'))
                common=(problem,capture['codes'],capture['logits'],encoding,identity,shared,structural,2.)
                routes={'raw':run_route('raw',*common),'structural_control':run_route('constrained',*common)}
                routes['guard_candidate']=run_semantic_route(routes['structural_control'],problem,capture['logits'],encoding,identity,literal,2.,literal_filter=unreachable_numeric_guard)
                tick=time.perf_counter();graph,h,reason=nearest_graph({'input':pair['input']},fit,capture['similarities'],encoding);build=time.perf_counter()-tick
                routes['nearest_training_graph']=run_route('nearest_training_graph',*common,baseline_graph=graph,baseline_hash=h,baseline_reason=reason,baseline_seconds=capture['embedding_seconds']+capture['retrieval_seconds'],baseline_construction_seconds=build)
                row=dict(device=device,uid=pair['uid'],routes=routes);rows.append(row);publish(OUT/f'decision-{device}-{i:04d}.json',row)
        publish(OUT/'decisions-seal.json',dict(contract_sha256=sha(OUT/'contract.json'),capture_seal_sha256=sha(OUT/'capture-seal.json'),decisions_sha256={p.name:sha(p) for p in sorted(OUT.glob('decision-*-????.json'))}))
        scored=[]
        for row in rows:
            pair=unique[row['uid']];problem=problem_for(pair);tests,_=development_tests.select(pair['uid'],load_hidden_tests(problem));assert mine.digest(tests)==pair['provenance']['independent_tests_sha256']
            score=dict(device=row['device'],uid=row['uid'],routes={a:score_fixed(r,problem,tests) for a,r in row['routes'].items()});scored.append(score);publish(OUT/f"score-{row['device']}-{row['uid'].replace(':','_')}.json",score)
        metrics={}
        for device in DEVICES:
            metrics[device]={}
            for arm in ARMS:
                values=[r['routes'][arm] for r in scored if r['device']==device];times=[r['timing']['total_seconds'] for r in values]
                metrics[device][arm]=dict(cases=10,correct=sum(r['accepted_correct'] for r in values),wrong=sum(r['wrong_acceptance'] for r in values),infrastructure=sum(r['infrastructure_failure'] for r in values),valid=sum(r['structurally_valid'] for r in values),abstentions=sum(r['decision']=='abstain' for r in values),p50=float(np.percentile(times,50)),p95=float(np.percentile(times,95)),maximum=max(times))
        by_device={d:{r['uid']:r['routes']['guard_candidate'] for r in scored if r['device']==d} for d in DEVICES}
        useful=[uid for uid in unique if by_device['cuda'][uid]['accepted_correct'] and not by_device['cpu'][uid]['accepted_correct']]
        harmful=[uid for uid in unique if by_device['cpu'][uid]['accepted_correct'] and not by_device['cuda'][uid]['accepted_correct']]
        gpu=metrics['cuda']['guard_candidate'];resources=monitor.counters();resources['threads']=2
        summary=dict(name=OUT.name,cpu_inference_reused_from='typed-gpu-reuse-fit-128-v1',metrics=metrics,useful=useful,harmful=harmful,parity=parity,setup=setups,resources=resources,actual_wall_seconds=time.perf_counter()-start,
                     development_gpu_reuse_pass=bool(gpu['correct']>=metrics['cpu']['guard_candidate']['correct'] and not harmful and not any(m['wrong'] or m['infrastructure'] for ds in metrics.values() for m in ds.values()) and gpu['p95']<=2),release_qualified=False,protected_opened=False,
                     rows=[dict(device=r['device'],uid=r['uid'],routes={a:dict(correct=v['accepted_correct'],wrong=v['wrong_acceptance'],reason=v['reason'],timing=v['timing']) for a,v in r['routes'].items()}) for r in scored])
        assert sources=={name:sha(ROOT/name) for name in sources},'Composition source drift'
        publish(OUT/'summary.json',summary);print(json.dumps({k:v for k,v in summary.items() if k not in ('rows','parity')},indent=2),flush=True)
    except BaseException as e:
        publish(OUT/'failure.json',dict(error=type(e).__name__,detail=str(e),resources=monitor.counters()));raise
    finally:monitor.stop.set()

if __name__=='__main__':main()
