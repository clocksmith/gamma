"""One fixed typed-predictor development run; protected graphs are never loaded."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import torch

from .. import validate
from ..embed import Embedder, EXPECTED_SHA256
from ..records import LANE_ROOT, Problem, load_hidden_tests, safe_name
from . import development_tests, typed_codec, typed_confirmation
from .typed_prediction_codec import PredictionCodec
from .typed_predictor import TypedPredictor, decisions, per_example_loss

INSTRUCTION='Instruct: Retrieve typed programming components that solve this task\nQuery: '


def signature(pair):
    tree=ast.parse(pair['input']['starter_code'])
    classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Solution']
    methods=[n for c in classes for n in c.body if isinstance(n,ast.FunctionDef) and n.name!='__init__']
    if len(methods)!=1: raise ValueError('Ambiguous development method signature')
    # Reconstruct a signature-only starter. Never embed the body of imported code.
    fn=methods[0]
    fn.body=[ast.Pass()]; fn.decorator_list=[]
    return fn.name,'class Solution:\n'+''.join('    '+line+'\n' for line in ast.unparse(fn).splitlines())


def query_text(pair):
    return pair['input']['statement']+'\n\n'+signature(pair)[1]


def problem_for(pair):
    method,_=signature(pair)
    return Problem(uid=pair['uid'],source='lcd',source_id=pair['uid'].split(':')[1],title='',
                   slug=pair['problem_family'],statement=pair['input']['statement'],io_mode='functional',
                   starter_code=pair['input']['starter_code'],entry={'class':'Solution','method':method},
                   params=pair['input']['params'],public_tests=pair['input']['public_examples'],
                   evidence_ceiling='independent_tests_passed',hidden_tests_path='tests/'+safe_name(pair['uid'])+'.json')


def score(pair,codes,encoding,identity,elapsed):
    problem=problem_for(pair); start=time.perf_counter()
    result={'decision':'abstain','first_prediction_correct':False,'wrong_acceptance':False}
    try:
        graph=encoding.decode(codes,[p[0] for p in problem.params])
        target=typed_codec.encode(graph,identity)
        source=typed_codec.render(target,identity,method=problem.entry['method'],params=[p[0] for p in problem.params])
    except (ValueError,TypeError,KeyError,IndexError,RecursionError) as error:
        return {**result,'reason':'invalid_prediction','error':str(error),
                'complete_seconds':elapsed+time.perf_counter()-start}
    result.update(structurally_valid=True,graph_sha256=typed_codec.digest(target))
    remaining=2.-elapsed-(time.perf_counter()-start)
    if remaining<=0:
        return {**result,'reason':'decision_budget','complete_seconds':elapsed+time.perf_counter()-start}
    public=validate.judge_problem(problem,source,problem.public_tests,wall_seconds=remaining)
    result.update(public=public.to_dict(),complete_seconds=elapsed+time.perf_counter()-start)
    result['decision']='answered' if public.passed and result['complete_seconds']<=2. else 'abstain'
    result['reason']='public_passed' if public.passed else 'public_failure'
    # Development scores only, from the same source-bound authorities used to
    # qualify labels. These outputs never become inference or retrieval inputs.
    if public.passed:
        tests,_=development_tests.select(pair['uid'],load_hidden_tests(problem))
        if typed_confirmation.mine.digest(tests)!=pair['provenance']['independent_tests_sha256']:
            raise ValueError('Development scoring authority changed')
        started=time.perf_counter(); verdict=validate.judge_problem(problem,source,tests)
        result.update(independent=verdict.to_dict(),independent_scoring_seconds=time.perf_counter()-started,
                      first_prediction_correct=verdict.passed,
                      wrong_acceptance=result['decision']=='answered' and not verdict.passed)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name',required=True)
    args=parser.parse_args()
    if not args.name.replace('-','').isalnum(): raise ValueError('Invalid run name')
    import transformers
    torch.set_num_threads(4); torch.manual_seed(17)
    assert torch.equal(torch.ones(2,2)@torch.ones(2,2),torch.full((2,2),2.))
    print(f'[compute] torch={torch.__version__} transformers={transformers.__version__} '
          f'cuda_available={torch.cuda.is_available()} cuda_count={torch.cuda.device_count()} target=cpu matmul=passed',flush=True)
    pairs_path=LANE_ROOT/'runs/typed-real-dev-v5/pairs.jsonl'
    identity=typed_codec.frozen(LANE_ROOT/'contracts/typed_codec_v1.json')
    pairs=typed_confirmation.verify_development(pairs_path,LANE_ROOT/'findings/typed-real-dev-v5/summary.json',identity)
    # Read the aggregate qualification receipt only. Neither teacher proposals,
    # protected target identities/graphs nor protected tests enter this process.
    qualified_path=LANE_ROOT/'findings/typed-confirmation-qualified-v1/summary.json'
    qualified=json.loads(qualified_path.read_text())
    if not qualified['teacher_qualification_complete'] or not qualified['qualified_targets'] or qualified['development_sha256']!=typed_confirmation.sha(pairs_path):
        raise ValueError('Protected qualification or fixed development gate missing')
    fit=[p for p in pairs if p['learning_split']=='development_fit']
    encoding=PredictionCodec.fit(fit)
    labels={k:torch.tensor([encoding.encode(p['target']['program'])[k] for p in fit])
            for k in encoding.encode(fit[0]['target']['program'])}
    unique={}
    for pair in pairs:
        if pair['uid'] in unique and pair['input']!=unique[pair['uid']]['input']:
            raise ValueError('Alternative targets have different requests')
        unique.setdefault(pair['uid'],pair)
    requests=list(unique.values()); indices={p['uid']:i for i,p in enumerate(requests)}
    fit_indices=[indices[p['uid']] for p in fit]
    groups=[[j for j,p in enumerate(fit) if p['uid']==uid] for uid in dict.fromkeys(p['uid'] for p in fit)]
    output=LANE_ROOT/'runs'/args.name; output.mkdir(exist_ok=False)
    sources={name:typed_confirmation.sha(Path(__file__).with_name(name)) for name in
             ('train_typed.py','typed_predictor.py','typed_prediction_codec.py')}
    contract={'schema':'algsolve.typed-student-development.v1','codec_sha256':identity,
              'dataset_sha256':typed_confirmation.sha(pairs_path),'qualification_receipt_sha256':typed_confirmation.sha(qualified_path),
              'prediction_encoding':encoding.descriptor(),'seed':17,'steps':400,'width':64,'layers':2,
              'optimizer':'AdamW','learning_rate':.001,'device':'cpu','threads':4,'configurations':1,
              'embedding_weights':EXPECTED_SHA256,'query_instruction':INSTRUCTION,
              'retrieval':'four frozen fit-graph descriptions; no audit targets or protected artifacts',
              'fit_graphs':len(fit),'fit_problems':len(groups),'audit_graphs':len(pairs)-len(fit),
              'alternative_loss':'minimum supervised loss over qualified graphs for the same problem',
              'decoder':'one parallel forward; independent argmax/bit threshold; invalid graph abstains without repair',
              'sources_sha256':sources,'protected_scoring':False,'selection':'fixed 400-step checkpoint; no sweep or audit-driven retries'}
    (output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    print(f'[run-contract] run_name={args.name} pairs_input_spec={pairs_path} resume_from=none resume_stage=none '
          'decode=parallel-argmax eval_dataset_paths=frozen-development-only device=cpu schedule=full_batch '
          'runtime_mode=cpu sweep_mode=after_train',flush=True)
    started=time.perf_counter(); embedder=Embedder(device='cpu'); cold=time.perf_counter()-started
    descriptions=[typed_codec.digest(p['target'])+' '+json.dumps(p['target']['program'],sort_keys=True) for p in fit]
    started=time.perf_counter(); contracts=embedder.encode(descriptions,batch_size=4)
    contract_embedding_seconds=time.perf_counter()-started
    vectors=[]; embedding_seconds=[]
    for p in requests:
        started=time.perf_counter(); vectors.append(embedder.encode([query_text(p)],query=True,instruction=INSTRUCTION)[0])
        embedding_seconds.append(time.perf_counter()-started)
    vectors=np.array(vectors); neighbors=np.argsort(-(vectors@contracts.T),axis=1,kind='stable')[:,:4]
    query=torch.from_numpy(vectors); memory=torch.from_numpy(contracts[neighbors])
    model=TypedPredictor(vectors.shape[1],encoding.slots,len(encoding.types))
    optimizer=torch.optim.AdamW(model.parameters(),lr=.001)
    started=time.perf_counter(); model.train()
    with (output/'metrics.jsonl').open('w') as stream:
        for step in range(400):
            optimizer.zero_grad(); logits=model(query[fit_indices],memory[fit_indices])
            per_target=per_example_loss(logits,labels)
            loss=torch.stack([per_target[g].min() for g in groups]).mean()
            loss.backward(); optimizer.step()
            if step==0 or (step+1)%20==0:
                metric={'step':step+1,'loss':float(loss.detach()),'elapsed_seconds':time.perf_counter()-started}
                stream.write(json.dumps(metric)+'\n'); stream.flush(); print('[train] '+json.dumps(metric),flush=True)
    training_seconds=time.perf_counter()-started
    torch.save({'state_dict':model.state_dict(),'contract':contract},output/'model.pt')
    checkpoint_sha=typed_confirmation.sha(output/'model.pt'); model.eval()
    # Freeze all predictions before reading any development scoring tests.
    predictions=[]
    with torch.inference_mode():
        for i,pair in enumerate(requests):
            started=time.perf_counter(); codes=decisions(model(query[i:i+1],memory[i:i+1])); seconds=time.perf_counter()-started
            predictions.append({'uid':pair['uid'],'split':pair['learning_split'],'codes':codes,
                                'prediction_seconds':seconds,'embedding_seconds':embedding_seconds[i]})
    (output/'predictions.jsonl').write_text(''.join(json.dumps(p)+'\n' for p in predictions))
    rows=[]
    with (output/'development_scores.jsonl').open('w') as stream:
        for pair,prediction in zip(requests,predictions):
            result=score(pair,prediction['codes'],encoding,identity,prediction['prediction_seconds']+prediction['embedding_seconds'])
            row={'uid':pair['uid'],'split':pair['learning_split'],**result}; rows.append(row)
            stream.write(json.dumps(row)+'\n'); stream.flush()
            print(json.dumps({'development_scored':len(rows),'total':len(requests),'correct':result['first_prediction_correct']}),flush=True)
    if typed_confirmation.sha(pairs_path)!=contract['dataset_sha256'] or typed_codec.frozen(LANE_ROOT/'contracts/typed_codec_v1.json')!=identity:
        raise ValueError('Frozen training inputs changed')
    summary={'schema':'algsolve.typed-student-development-summary.v1','checkpoint_sha256':checkpoint_sha,
             'parameters':sum(p.numel() for p in model.parameters()),'prediction_slots':encoding.slots,
             'training_seconds':training_seconds,'cold_embedding_load_seconds':cold,
             'fit_contract_embedding_seconds':contract_embedding_seconds,'student_trained':True,'protected_scored':False,
             'graph_head_p50_seconds':float(np.median([p['prediction_seconds'] for p in predictions])),
             'splits':{},'artifacts_sha256':{name:typed_confirmation.sha(output/name) for name in
                                           ('contract.json','predictions.jsonl','development_scores.jsonl','metrics.jsonl')},
             'limits':['One fixed configuration on 10 development fit problems; not a learned generalization claim.',
                       'Protected targets and tests were not loaded; no protected score exists.',
                       'Reported decision timing uses per-request warm embedding plus prediction, assembly and public checks; fit retrieval setup is separate.',
                       'One forward over primitive tree slots; invalid syntax/type/effects abstain without repair.',
                       'Equivalent teacher alternatives share one problem loss; exact teacher equality is not the correctness criterion.'],
             'next_gate':'Implement matched deterministic search and seal all route/checkpoint artifacts before protected scoring.'}
    for label in ('development_fit','development_audit'):
        selected=[r for r in rows if r['split']==label]
        summary['splits'][label]={'problems':len(selected),'structurally_valid':sum(r.get('structurally_valid',False) for r in selected),
                                 'first_prediction_correct':sum(r['first_prediction_correct'] for r in selected),
                                 'answered':sum(r['decision']=='answered' for r in selected),
                                 'wrong_acceptance':sum(r['wrong_acceptance'] for r in selected),
                                 'complete_p50_seconds':float(np.median([r['complete_seconds'] for r in selected])),
                                 'complete_p95_seconds':float(np.percentile([r['complete_seconds'] for r in selected],95))}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
