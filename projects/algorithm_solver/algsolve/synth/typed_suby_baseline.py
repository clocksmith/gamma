"""Nearest-compatible-fit-graph DEVELOPMENT baseline; no training or prediction."""
from pathlib import Path
import argparse
import json
import os
import time

from ..records import LANE_ROOT
from ..rebuild_recognition import Monitor, publish, bound_receipt, sha, digest
from . import typed_codec, typed_confirmation
from .typed_comparison import nearest_graph, run_route, score_fixed
from .typed_prediction_codec import PredictionCodec

NAME='typed-lcd-suby-nearest-v1'
DATA=LANE_ROOT/'runs/typed-lcd-suby-development-v1'
OUTPUT=LANE_ROOT/'runs'/NAME
ASSET=LANE_ROOT/'data/reconstruction/recognition-rebuild-dev-suby-v1'


def load(path):return json.loads(path.read_text())


def requests_for(pairs):
    import copy
    unique={}
    for pair in pairs:
        public={k:copy.deepcopy(pair[k]) for k in ('uid','problem_family','learning_split','input')}
        if pair['uid'] in unique and unique[pair['uid']]!=public:
            raise ValueError('Alternative graphs disagree about public request or partition')
        unique.setdefault(pair['uid'],public)
    return list(unique.values())


def run(monitor):
    identity=typed_codec.frozen(LANE_ROOT/'contracts/typed_codec_v1.json')
    pairs=typed_confirmation.verify_development(DATA/'pairs.jsonl',DATA/'summary.json',identity)
    sources={str(p.relative_to(LANE_ROOT)):sha(p) for p in (LANE_ROOT/'algsolve').rglob('*.py')}
    import importlib.metadata,sys
    from ..rebuild_download import FILES,verify
    contract={'dependencies':{n:importlib.metadata.version(n) for n in ('torch','transformers','numpy')},'python':sys.executable,
        'payloads':{name:verify(ASSET/name,spec) for name,spec in FILES.items()},'schema':'algsolve.typed-lcd-nearest-development.v1','name':NAME,'codec_sha256':identity,
        'corpus_sha256':sha(DATA/'pairs.jsonl'),'qualification_sha256':sha(DATA/'summary.json'),
        'test_authorities_sha256':sha(DATA/'test-authorities.json'),'sources_sha256':sources,
        'embedding':'existing pinned Qwen3-Embedding-0.6B; CPU four threads',
        'route':'Nearest interface/type-compatible frozen development-fit graph; positional alpha-renaming only; no graph edits.',
        'budget_seconds':2.,'training':False,'protected_scoring':False,'historical_reproduction':False,
        'evidence':'Development baseline, not learned prediction, fresh confirmation or arbitrary unseen solving.'}
    publish(OUTPUT/'contract.json',contract)
    if (OUTPUT/'summary.json').exists():
        saved=load(OUTPUT/'summary.json')
        if any(sha(OUTPUT/n)!=h for n,h in saved['artifacts_sha256'].items()):raise ValueError('Completed baseline artifact drift')
        print(json.dumps({'completed_resume':True,'summary_sha256':sha(OUTPUT/'summary.json')}));return
    import numpy as np
    import torch
    from ..embed import Embedder
    from .train_typed import query_text, problem_for, INSTRUCTION
    torch.set_num_threads(4);torch.set_num_interop_threads(1)
    if not torch.equal(torch.ones(2,2)@torch.ones(2,2),torch.full((2,2),2.)):raise ValueError('CPU probe failed')
    print(json.dumps({'python':__import__('sys').executable,'torch':torch.__version__,'cuda_available':torch.cuda.is_available(),'cuda_count':torch.cuda.device_count(),'device':'cpu'}),flush=True)
    fit=[p for p in pairs if p['learning_split']=='development_fit'];encoding=PredictionCodec.fit(fit)
    requests=requests_for(pairs)
    started=time.perf_counter();embedder=Embedder(device='cpu');load_seconds=time.perf_counter()-started
    started=time.perf_counter()
    descriptions=[typed_codec.digest(p['target'])+' '+json.dumps(p['target']['program'],sort_keys=True) for p in fit]
    memory=embedder.encode(descriptions,batch_size=1);memory_seconds=time.perf_counter()-started
    publish(OUTPUT/'setup.json',{'encoder_load_hash_seconds':load_seconds,'fit_graph_embedding_seconds':memory_seconds,
        'fit_graphs':len(fit),'fit_problems':len({p['uid'] for p in fit}),'prediction_descriptor':encoding.descriptor()})
    decision_dir=OUTPUT/'decisions';decision_dir.mkdir(exist_ok=True);decisions=[]
    for i,request in enumerate(requests):
        binding={'contract_sha256':sha(OUTPUT/'contract.json'),'request_sha256':digest(request)}
        def decide():
            started=time.perf_counter();vector=embedder.encode([query_text(request)],query=True,instruction=INSTRUCTION)[0]
            similarities=memory@vector;retrieved=time.perf_counter()
            graph,h,reason=nearest_graph(request,fit,similarities,encoding);constructed=time.perf_counter()
            result=run_route('nearest_training_graph',problem_for(request),None,None,encoding,identity,0.,{},2.,
                 baseline_graph=graph,baseline_hash=h,baseline_reason=reason,
                 baseline_seconds=retrieved-started,baseline_construction_seconds=constructed-retrieved)
            return {'uid':request['uid'],'split':request['learning_split'],'result':result}
        row=bound_receipt(decision_dir/f'{i:04d}.json',binding,decide);decisions.append(row)
        print(json.dumps({'decided':request['uid'],'decision':row['result']['decision'],'reason':row['result']['reason'],**monitor.counters()}),flush=True)
    publish(OUTPUT/'decisions-seal.json',{'contract_sha256':sha(OUTPUT/'contract.json'),'decisions':{p.name:sha(p) for p in decision_dir.glob('*.json')}})
    authorities=load(DATA/'test-authorities.json');scores=[];score_dir=OUTPUT/'scoring';score_dir.mkdir(exist_ok=True)
    for i,(request,decision) in enumerate(zip(requests,decisions)):
        binding={'seal_sha256':sha(OUTPUT/'decisions-seal.json'),'decision_sha256':digest(decision),'test_authority_sha256':digest(authorities[request['uid']])}
        row=bound_receipt(score_dir/f'{i:04d}.json',binding,lambda:{'uid':request['uid'],'split':request['learning_split'],
              'result':score_fixed(decision['result'],problem_for(request),authorities[request['uid']]['tests'])})
        scores.append(row)
    if sources!={str(p.relative_to(LANE_ROOT)):sha(p) for p in (LANE_ROOT/'algsolve').rglob('*.py')}:raise ValueError('Baseline source drift')
    summary={'schema':'algsolve.typed-lcd-nearest-development-summary.v1','name':NAME,'contract_sha256':sha(OUTPUT/'contract.json'),
       'splits':{},'resource_counters':monitor.counters(),'setup':load(OUTPUT/'setup.json'),'training':False,'protected_scored':False,'historical_reproduction':False,
       'next_action':'Compare this exact baseline with a separately authorized newly trained raw/corrected predictor; no protected opening.',
       'limitations':['Only nearest fit-graph reuse, no learned composition or test-driven search.','18 previously examined development problems, finite source tests, shared host.','An independently correct abstained program is not an accepted correct answer.']}
    for split in ('development_fit','development_audit'):
        rs=[r['result'] for r in scores if r['split']==split];ts=[r['timing']['total_seconds'] for r in rs]
        summary['splits'][split]={'requests':len(rs),'accepted_correct':sum(r['accepted_correct'] for r in rs),
            'wrong_acceptances':sum(r['wrong_acceptance'] for r in rs),'abstentions':sum(r['decision']=='abstain' for r in rs),
            'infrastructure_failures':sum(r['infrastructure_failure'] for r in rs),
            'p50_seconds':float(np.percentile(ts,50)),'p95_seconds':float(np.percentile(ts,95)),'maximum_seconds':max(ts)}
    summary['artifacts_sha256']={str(p.relative_to(OUTPUT)):sha(p) for p in OUTPUT.rglob('*') if p.is_file() and p.name!='lock' and 'failures' not in p.parts}
    publish(OUTPUT/'summary.json',summary);print(json.dumps(summary,indent=2),flush=True)


def main():
    import fcntl
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--name',choices=[NAME],required=True);parser.parse_args()
    os.environ['ALGSOLVE_EMBEDDING_DIR']=str(ASSET/'encoder');os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    OUTPUT.mkdir(exist_ok=True);lock=(OUTPUT/'lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    monitor=Monitor([ASSET,LANE_ROOT/'runs']);monitor.start()
    print(f'[run-contract] run_name={NAME} pairs_input_spec=typed-lcd-suby-development-v1 resume_from=atomic-stage-receipts resume_stage=existing decode=nearest-compatible-fit-graph eval_dataset_paths=development-only device=cpu schedule=serial runtime_mode=reviewed-linux-sandbox sweep_mode=none training=none',flush=True)
    try:run(monitor)
    except BaseException as error:
        d=OUTPUT/'failures';d.mkdir(exist_ok=True);publish(d/f'{time.time_ns()}.json',{'type':type(error).__name__,'detail':str(error),'resources':monitor.counters()});raise
    finally:monitor.stop.set()

if __name__=='__main__':main()
