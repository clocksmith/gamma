"""One separately named, fixed CPU development training proposal.

freeze prepares a reviewable contract without training. train needs external
owner authorization; this CLI is not itself an authorization mechanism.
Historical assets and protected cases are never loaded or substituted.
"""
import argparse
import io
import json
import os
from pathlib import Path
import time

from ..records import LANE_ROOT
from ..rebuild_recognition import Monitor, publish, sha
from . import typed_codec, typed_confirmation
from .typed_prediction_codec import PredictionCodec
from .typed_suby_baseline import requests_for

NAME='typed-lcd-student-suby-v1'
DATA=LANE_ROOT/'runs/typed-lcd-suby-development-v1'
OUTPUT=LANE_ROOT/'runs'/NAME
ASSET=LANE_ROOT/'data/reconstruction/recognition-rebuild-dev-suby-v1'
PROPOSAL=LANE_ROOT/'contracts/typed_lcd_suby_training_proposal_v1.json'


def load(path):return json.loads(path.read_text())


def training_view(pairs):
    fit=[p for p in pairs if p['learning_split']=='development_fit']
    requests=requests_for(pairs)
    indices={p['uid']:i for i,p in enumerate(requests)}
    groups=[[i for i,p in enumerate(fit) if p['uid']==uid] for uid in dict.fromkeys(p['uid'] for p in fit)]
    return fit,requests,[indices[p['uid']] for p in fit],groups


def freeze():
    import importlib.metadata,sys
    from ..rebuild_download import FILES,verify
    identity=typed_codec.frozen(LANE_ROOT/'contracts/typed_codec_v1.json')
    pairs=typed_confirmation.verify_development(DATA/'pairs.jsonl',DATA/'summary.json',identity)
    if not load(DATA/'summary.json')['training_ready']:raise ValueError('New development corpus is not qualified')
    proposal=load(PROPOSAL)
    if sha(DATA/'pairs.jsonl')!=proposal['corpus_sha256']:raise ValueError('Proposed corpus changed')
    fit,requests,indices,groups=training_view(pairs);encoding=PredictionCodec.fit(fit)
    contract={'schema':'algsolve.typed-lcd-suby-training.v1','name':NAME,
        'proposal_sha256':sha(PROPOSAL),'dataset_sha256':sha(DATA/'pairs.jsonl'),
        'qualification_sha256':sha(DATA/'summary.json'),'codec_sha256':identity,
        'prediction_encoding':encoding.descriptor(),'seed':17,'steps':400,'width':64,'layers':2,
        'optimizer':'AdamW','learning_rate':.001,'device':'cpu','threads':4,'configurations':1,
        'fit_graphs':len(fit),'fit_problems':len(groups),'audit_graphs':len(pairs)-len(fit),'requests':len(requests),
        'retrieval':'four frozen fit graphs only; same representation as the completed nearest baseline',
        'alternative_loss':'minimum supervised loss over qualified fit graphs for each problem',
        'checkpoint_selection':'fixed step400 only; no audit scoring, sweep or adaptive retries',
        'sources_sha256':{str(p.relative_to(LANE_ROOT)):sha(p) for p in (LANE_ROOT/'algsolve').rglob('*.py')},
        'payloads':{n:verify(ASSET/n,s) for n,s in FILES.items()},
        'dependencies':{n:importlib.metadata.version(n) for n in ('torch','transformers','numpy')},'python':sys.executable,
        'protected_scoring':False,'historical_reproduction':False,'nearby_variants_loaded':False,
        'limits':proposal['limits']}
    publish(OUTPUT/'contract.json',contract)
    return contract,pairs,fit,requests,indices,groups,encoding


def train(monitor):
    contract,pairs,fit,requests,fit_indices,groups,encoding=freeze()
    if (OUTPUT/'summary.json').exists():
        summary=load(OUTPUT/'summary.json')
        if any(sha(OUTPUT/n)!=h for n,h in summary['artifacts_sha256'].items()):raise ValueError('Completed training drift')
        print(json.dumps({'completed_resume':True,'checkpoint_sha256':summary['checkpoint_sha256']}));return
    if (OUTPUT/'training-started.json').exists():
        raise ValueError('Interrupted training retained; do not silently repeat. Propose explicit resume from saved evidence.')
    import numpy as np
    import torch
    from ..embed import Embedder
    from .train_typed import query_text,INSTRUCTION
    from .typed_predictor import TypedPredictor,per_example_loss
    from .typed_scoring import write_bytes_once
    torch.set_num_threads(4);torch.set_num_interop_threads(1);torch.manual_seed(17)
    if not torch.equal(torch.ones(2,2)@torch.ones(2,2),torch.full((2,2),2.)):raise ValueError('CPU probe failed')
    print(json.dumps({'python':__import__('sys').executable,'torch':torch.__version__,'cuda_available':torch.cuda.is_available(),'cuda_count':torch.cuda.device_count(),'device':'cpu'}),flush=True)
    started=time.perf_counter();embedder=Embedder(device='cpu');cold=time.perf_counter()-started
    texts=[typed_codec.digest(p['target'])+' '+json.dumps(p['target']['program'],sort_keys=True) for p in fit]
    started=time.perf_counter();memory=embedder.encode(texts,batch_size=1);memory_seconds=time.perf_counter()-started
    vectors=[];query_times=[]
    for request in requests:
        started=time.perf_counter();vectors.append(embedder.encode([query_text(request)],query=True,instruction=INSTRUCTION)[0]);query_times.append(time.perf_counter()-started)
    vectors=np.array(vectors);neighbors=np.array([np.argsort(-(memory@v),kind='stable')[:4] for v in vectors])
    query=torch.from_numpy(vectors);retrieved=torch.from_numpy(memory[neighbors])
    example=encoding.encode(fit[0]['target']['program'])
    labels={k:torch.tensor([encoding.encode(p['target']['program'])[k] for p in fit]) for k in example}
    model=TypedPredictor(vectors.shape[1],encoding.slots,len(encoding.types),width=64)
    optimizer=torch.optim.AdamW(model.parameters(),lr=.001)
    publish(OUTPUT/'training-started.json',{'contract_sha256':sha(OUTPUT/'contract.json'),'parameters':sum(p.numel() for p in model.parameters())})
    metrics=[];started=time.perf_counter();model.train()
    for step in range(400):
        optimizer.zero_grad();logits=model(query[fit_indices],retrieved[fit_indices]);losses=per_example_loss(logits,labels)
        loss=torch.stack([losses[g].min() for g in groups]).mean();loss.backward();optimizer.step()
        if step==0 or (step+1)%20==0:
            row={'step':step+1,'loss':float(loss.detach()),'elapsed_seconds':time.perf_counter()-started};metrics.append(row)
            print('[train] '+json.dumps(row),flush=True)
    training_seconds=time.perf_counter()-started
    if contract['sources_sha256']!={str(p.relative_to(LANE_ROOT)):sha(p) for p in (LANE_ROOT/'algsolve').rglob('*.py')}:raise ValueError('Training source drift')
    data=io.BytesIO();torch.save({'state_dict':model.state_dict(),'contract':contract},data);write_bytes_once(OUTPUT/'model.pt',data.getvalue())
    write_bytes_once(OUTPUT/'metrics.jsonl',''.join(json.dumps(r)+'\n' for r in metrics).encode())
    summary={'schema':'algsolve.typed-lcd-suby-student-summary.v1','name':NAME,'checkpoint_sha256':sha(OUTPUT/'model.pt'),
        'parameters':sum(p.numel() for p in model.parameters()),'training_seconds':training_seconds,
        'encoder_load_hash_seconds':cold,'fit_contract_embedding_seconds':memory_seconds,'query_embedding_seconds':sum(query_times),
        'training_completed':True,'prediction_scored':False,'protected_scored':False,'historical_reproduction':False,
        'resource_counters':monitor.counters(),'next_action':'Freeze and run one matched raw/constrained/nearest development comparison; training loss is not solving correctness.',
        'artifacts_sha256':{n:sha(OUTPUT/n) for n in ('model.pt','metrics.jsonl','contract.json','training-started.json')}}
    publish(OUTPUT/'summary.json',summary);print(json.dumps(summary,indent=2),flush=True)


def main():
    import fcntl
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['freeze','train']);args=parser.parse_args()
    OUTPUT.mkdir(exist_ok=True);lock=(OUTPUT/'lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    os.environ['ALGSOLVE_EMBEDDING_DIR']=str(ASSET/'encoder');os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    if args.action=='freeze':
        freeze();print(json.dumps({'frozen_training_contract_sha256':sha(OUTPUT/'contract.json'),'training_started':False}));return
    monitor=Monitor([ASSET,LANE_ROOT/'runs']);monitor.start()
    print(f'[run-contract] run_name={NAME} pairs_input_spec=typed-lcd-suby-development-v1 resume_from=none resume_stage=none decode=parallel-argmax eval_dataset_paths=development-only device=cpu schedule=full-batch runtime_mode=cpu sweep_mode=after-train',flush=True)
    try:train(monitor)
    except BaseException as error:
        d=OUTPUT/'failures';d.mkdir(exist_ok=True);publish(d/f'{time.time_ns()}.json',{'type':type(error).__name__,'detail':str(error),'resources':monitor.counters()});raise
    finally:monitor.stop.set()

if __name__=='__main__':main()
