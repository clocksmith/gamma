from pathlib import Path
import os,time,json,hashlib,sys
root=Path('/home/clocksmith/deco/gamma/projects/algorithm_solver')
asset=root/'data/reconstruction/recognition-rebuild-dev-suby-v1'
os.environ['ALGSOLVE_EMBEDDING_DIR']=str(asset/'encoder')
from algsolve.rebuild_recognition import Monitor,publish,sha
name='typed-lcd-suby-cache-diagnostic-v1';out=root/'runs'/name
out.mkdir(exist_ok=True)
assert not (out/'summary.json').exists(),'Finite diagnostic already completed; no repeat'
monitor=Monitor([asset,root/'runs']);monitor.start()
print(f'[run-contract] run_name={name} pairs_input_spec=existing-public-development-longest-request resume_from=none resume_stage=none decode=none eval_dataset_paths=development-input-only device=cpu schedule=one_default_then_one_cache_off runtime_mode=cpu sweep_mode=none training=none',flush=True)
try:
 import torch,numpy as np,transformers
 from algsolve.embed import Embedder,MAX_TOKENS
 from algsolve.synth.typed_suby_baseline import requests_for
 from algsolve.synth.train_typed import query_text,INSTRUCTION
 from transformers import AutoTokenizer
 torch.set_num_threads(4);torch.set_num_interop_threads(1)
 assert torch.equal(torch.ones(2,2)@torch.ones(2,2),torch.full((2,2),2.))
 pairs=[json.loads(line) for line in (root/'runs/typed-lcd-suby-development-v1/pairs.jsonl').read_text().splitlines()]
 requests=requests_for(pairs)
 tok=AutoTokenizer.from_pretrained(asset/'encoder',padding_side='left',local_files_only=True)
 texts=[INSTRUCTION+query_text(p) for p in requests]
 counts=[len(tok(t)['input_ids']) for t in texts]
 i=max(range(len(counts)),key=counts.__getitem__);request=requests[i];text=texts[i]
 assert max(counts)<MAX_TOKENS
 contract={'name':name,'parent_commit':'36404d2a1a254a787ca7a91d215790abbaec6b82','purpose':'One paired default KV-cache versus disabled KV-cache diagnostic on longest existing public development request; not a route qualification or new model.', 'selection':'Largest token count among the retained 18 unique public development requests, independent of verdicts.','selected_uid':request['uid'],'selected_input_sha256':hashlib.sha256(text.encode()).hexdigest(),'counts_by_uid':dict(zip([r['uid'] for r in requests],counts)),'pairs_sha256':sha(root/'runs/typed-lcd-suby-development-v1/pairs.jsonl'),'script_sha256':sha(Path(__file__)),'encoder_code_sha256':sha(root/'algsolve/embed.py'),'encoder_config_sha256':sha(asset/'encoder/config.json'),'tokenizer_sha256':sha(asset/'encoder/tokenizer.json'),'torch':torch.__version__,'transformers':transformers.__version__,'cuda_available':torch.cuda.is_available(),'cuda_count':torch.cuda.device_count(),'device':'cpu','threads':4,'input_batch_size':1,'truncation':False,'arm_order':['default_cache','cache_disabled'],'quality_check':'Bitwise normalized vector equality on the same full input; no source/test/graph/threshold changes.','limits':{'rss_bytes':8*1024**3,'disk_bytes':5*1024**3,'wall_seconds':900},'protected_opened':False,'training':False,'downloads':False}
 publish(out/'contract.json',contract)
 t=time.perf_counter();e=Embedder(device='cpu');loading=time.perf_counter()-t
 warm=time.perf_counter();e.encode(['Return an integer unchanged.'],query=True,instruction=INSTRUCTION);warm=time.perf_counter()-warm
 enc=e.tokenizer([text],padding=True,truncation=True,max_length=MAX_TOKENS,return_tensors='pt').to('cpu')
 assert enc['input_ids'].shape==(1,counts[i])
 rows=[];vectors=[]
 for arm in contract['arm_order']:
  t=time.perf_counter()
  with torch.no_grad():
   output=e.model(**enc,**({} if arm=='default_cache' else {'use_cache':False}))
  forward=time.perf_counter()-t
  pooled=torch.nn.functional.normalize(output.last_hidden_state[:,-1].float(),dim=-1).cpu().numpy().copy()
  cache=getattr(output,'past_key_values',None)
  rows.append({'arm':arm,'forward_seconds':forward,'cache_returned':cache is not None,'cache_sequence_length':cache.get_seq_length() if cache is not None else None,'vector_sha256':hashlib.sha256(pooled.tobytes()).hexdigest()})
  vectors.append(pooled);np.save(out/(arm+'.npy'),pooled,allow_pickle=False)
  del output,cache
  print(json.dumps(rows[-1]),flush=True)
 result={'contract_sha256':sha(out/'contract.json'),'selected_uid':request['uid'],'tokens':counts[i],'batch_size':1,'truncated':False,'encoder_load_seconds':loading,'short_warmup_seconds':warm,'arms':rows,'vectors_bitwise_equal':np.array_equal(*vectors),'maximum_absolute_difference':float(np.max(np.abs(vectors[0]-vectors[1]))),'cache_disabled_alone_exceeds_two_second_budget':rows[1]['forward_seconds']>2.,'resource_counters':monitor.counters(),'limitations':['One pair on a shared host; order fixed, no repetition and no causal speedup claim.','Forward phase only; complete route also needs tokenization/ranking/assembly/public execution.','Vector equality on one full development input is not global numerical or quality qualification.']}
 publish(out/'summary.json',result);print(json.dumps(result,indent=2),flush=True)
finally:monitor.stop.set()
