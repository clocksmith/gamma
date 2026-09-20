from pathlib import Path
import json,hashlib,sys,math
import numpy as np
sys.path.insert(0,'projects/enwiki9/src')
from gamma_enwiki9.adapters.fx2_numeric_reference import read_trace,loss_bits
r=Path('projects/enwiki9').resolve();name='fx2_numeric_attribution2048_q0_v1';out=r/'results'/name
ref=lambda p:{'path':p.relative_to(r).as_posix(),'sha256':'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()}
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
manifest=json.loads((out/'artifacts.json').read_bytes())
for v in manifest['artifacts']:
 p=r/v['path'];assert p.stat().st_size==v['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
comparison=json.loads((out/'comparison.json').read_bytes())
report={'schema':'gamma.enwiki9.fixed-numerical-analysis.v1','comparison':ref(out/'comparison.json'),'verified_artifacts':len(manifest['artifacts']),'fixtures':{},'objective_credit_bytes':0,'training_performed':False,'interpretation':'Both implementations find E worse on both frozen populations. Mismatch reduces the measured regression; parity alone cannot make this checkpoint improve on these fixtures. Final mixer, prior 1MB archive loss and full corpus are not attributed by this diagnostic.'}
for fixture,item in comparison['fixtures'].items():
 f=out/'numeric'/fixture;tm=np.fromfile(f/'tokens-markers.bin',dtype='u1').reshape(-1,2);tokens,markers=tm.T
 v={'prediction_count':int(np.count_nonzero(markers[:-1]!=2)),'rows':len(tokens),'delta_reference_bits':item['delta_reference_bits'],'delta_native_bits':item['delta_native_bits'],'delta_mismatch_bits':item['delta_mismatch_bits'],'arms':{}}
 for arm,a in item['arms'].items():
  p=f/arm;n,order=read_trace(p/'native.trace');q,_=read_trace(p/'reference.trace')
  native=np.fromfile(p/'base.f32',dtype='<f4').reshape(-1,410);reference=np.fromfile(p/'reference-plain.f32',dtype='<f4').reshape(-1,410)
  for label,data in [('native',native),('reference',reference)]:assert loss_bits(data[:,205:],tokens,markers)[0]==a[label+'_loss']
  differing=[(row,key,int(np.flatnonzero(n[row,key]!=q[row,key])[0])) for row,key in order if np.any(n[row,key]!=q[row,key])]
  row,key,i=differing[0]
  first={'row':row,'key':key,'coordinate':i,'native':float(n[row,key][i]),'reference':float(q[row,key][i])}
  d=a['first_integer_difference'];row=d['row'];module=d['key'].removesuffix('.quantize_activation.integer')
  linear={}
  for suffix in ['.accumulator','.output']:
   x,y=n[row,module+suffix],q[row,module+suffix];indices=np.flatnonzero(x!=y)
   z=int(indices[0]) if len(indices) else 0
   linear[suffix]={'coordinate':z,'native':float(x[z]),'reference':float(y[z]),'different_elements':len(indices)}
  interventions=a['interventions']['integer']['steps'];last=interventions[-1]
  after=np.fromfile(p/f'integer-{len(interventions)}.probabilities.f32',dtype='<f4').reshape(-1,205)
  v['arms'][arm]={'native_loss_bits':a['native_loss']['bits'],'reference_loss_bits':a['reference_loss']['bits'],'first_numerically_unequal_observation':first,'first_bit_difference':a['first_compared_bit_difference'],'first_integer_difference':d,'first_divergent_quantizer_linear_followthrough':linear,'integer_substitutions':len(interventions),'remaining_traced_integer_difference':a['interventions']['integer']['remaining_compared_difference'],'remaining_full_fixture_logit_max':last['remaining_logit_max'],'reference_loss_after_integer_substitutions':last['reference_loss_after']['bits'],'baseline_max_logit_difference':float(np.max(np.abs(native[:,:205]-reference[:,:205]))),'baseline_max_probability_difference_first64':float(np.max(np.abs(native[:64,205:]-reference[:64,205:]))),'after_max_probability_difference_first64':float(np.max(np.abs(native[:64,205:]-after[:64]))),'parameters_unchanged':a['parameters_unchanged'],'decoded_tensors_equal':a['decoded_tensors_equal']}
 report['fixtures'][fixture]=v
p=out/'numeric/synthetic/P';n,_=read_trace(p/'native.trace');q,_=read_trace(p/'reference.trace')
report['synthetic_P_precursor']={'row':5,'coordinate':634,'operation':'blocks.3.mlp.up','integer_dot_native':float(n[5,'blocks.3.mlp.up.accumulator'][634]),'integer_dot_reference_reconstructed':float(q[5,'blocks.3.mlp.up.accumulator'][634]),'rescaled_native':float(n[5,'blocks.3.mlp.up.output'][634]),'rescaled_reference':float(q[5,'blocks.3.mlp.up.output'][634]),'explanation':'Quantized input integers and decoded weights agree here. Native computes integer dot then folded-scale rescaling; reference accumulates dequantized FP32 products. The outputs differ before ReLU squared and the downstream half-integer boundary.'}
job_path=r/'operations/adaptive/completed/959_20260920T023220Z_bded1a9e05.json';job=json.loads(job_path.read_bytes());guard_path=r/job['execution_resources']['guard_path'];guard=json.loads(guard_path.read_bytes())
assert job['returncode']==0 and job['execution_resources']['cleanup_complete'] and guard['status']=='complete' and not any(guard['guards'].values())
report['job']=ref(job_path);report['guard']=ref(guard_path);report['resources']={'elapsed_seconds':guard['elapsed_s'],'peak_cgroup_bytes':guard['peaks']['cgroup_memory_peak_bytes'],'peak_scratch_allocated_bytes':guard['peaks']['max_sampled_scratch_allocated_bytes'],'cleanup_complete':True,'timing_authority':'diagnostic'}
write(out/'analysis.json',report)
revision={'candidateId':name,'candidateTreeSha256':job['candidate_tree_sha256'],'receipt':job['candidate_revision']}
index={'schema':'gamma.enwiki9.terminal-result-index.v1','job':ref(job_path),'guard':ref(guard_path),'arms':[],'evidence':[ref(out/'comparison.json'),ref(out/'analysis.json'),ref(out/'artifacts.json')]}
for fixture,item in comparison['fixtures'].items():
 for arm,a in item['arms'].items():
  label=fixture+'-'+arm;p=out/(label+'.driver.json')
  value={'program_id':name,'program_name':'Fixed P/E numerical attribution','arm':label,'candidate_revision':revision,'timestamp':job['finished_at'],'run_source':job_path.relative_to(r).as_posix(),'run_purpose':'diagnostic','run_scope_label':fixture+'-modeled-token-rows','run_context':'Fixed neural head replay; no optimizer, codec archive, inverse or full-corpus score. Both implementations use identical tokens, priors and resets.','run_tags':['fixed-checkpoint','numeric-attribution','zero-score-credit'], 'data_size':None,'compressed_size':None,'roundtrip_ok':None,'determinism':None,'hutter_score':None,'scope_symbols':item['rows'],'prediction_count':a['native_loss']['predictions'],'measurements':a,'missing_diagnostics':['No final-mixer or archive measurement','No whole-fixture numerical parity; only first 64 rows traced','No complete package or full corpus score']}
  write(p,value);index['arms'].append({'arm':label,'result':ref(p),'artifacts':{'native_predictions':ref(out/'numeric'/fixture/arm/'base.f32'),'reference_predictions':ref(out/'numeric'/fixture/arm/'reference-plain.f32'),'native_trace':ref(out/'numeric'/fixture/arm/'native.trace'),'reference_trace':ref(out/'numeric'/fixture/arm/'reference.trace')}})
write(out/'terminal-index.json',index)
print(json.dumps({'verified_artifacts':report['verified_artifacts'],'resources':report['resources'],'synthetic_precursor':report['synthetic_P_precursor']},indent=2))
