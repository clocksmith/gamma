from pathlib import Path
import json,hashlib,math
import numpy as np
r=Path('projects/enwiki9').resolve();n='fx2_native_forward2048_q0_v1';o=r/'results'/n
ref=lambda p:{'path':p.relative_to(r).as_posix(),'sha256':'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()}
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
j=json.loads((o/'comparison.json').read_bytes());manifest=json.loads((o/'artifacts.json').read_bytes())
for a in manifest['artifacts']:
 p=r/a['path'];assert p.stat().st_size==a['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256']
job_path=r/'operations/adaptive/completed/959_20260920T025512Z_a4dd4d31c3.json';job=json.loads(job_path.read_bytes());guard_path=r/job['execution_resources']['guard_path'];g=json.loads(guard_path.read_bytes())
assert job['returncode']==0 and job['execution_resources']['cleanup_complete'] and g['status']=='complete' and not any(g['guards'].values())
report={'schema':'gamma.enwiki9.native-forward-terminal.v1','comparison':ref(o/'comparison.json'),'verified_artifacts':len(manifest['artifacts']),'job':ref(job_path),'guard':ref(guard_path),'all_forward_values_bitwise_native':True,'training_performed':False,'optimizer_updates':0,'gradient_native_exact':False,'internal_torch_state_parity_established':False,'objective_credit_bytes':0,'fixtures':{},'resources':{'elapsed_seconds':g['elapsed_s'],'peak_cgroup_bytes':g['peaks']['cgroup_memory_peak_bytes'],'peak_scratch_allocated_bytes':g['peaks']['max_sampled_scratch_allocated_bytes'],'cleanup_complete':True,'timing_authority':'diagnostic'},'next_action':'Separately freeze matched data-only versus joint-cost training using this native forward and explicitly approximate backward; judge actual packed files and native archives. This result does not establish useful gradients or compression gain.'}
for f,item in j['fixtures'].items():
 hashes={};summary={};total=0
 for arm,m in item['arms'].items():
  path=o/'numeric/calls'/(f+'-'+arm);receipt=json.loads((path/'forward.json').read_bytes());values=np.fromfile(path/'predictions.f32',dtype='<f4').reshape(-1,410);tm=np.fromfile(path/'tokens-markers.bin',dtype='u1').reshape(-1,2)
  selected='P' if arm=='P-repeat' else arm
  expected=o/'snapshot'/j['plan']['baseline']/f/selected/'base.f32'
  assert (path/'predictions.f32').read_bytes()==expected.read_bytes()
  bits=math.fsum(-math.log(float(values[i,205+int(tm[i+1,0])]),2) for i in range(len(tm)-1) if tm[i,1]!=2)
  assert abs(bits-m['corrected_loss_bits'])<1e-10
  hashes[arm]=receipt['weights_sha256'];total+=values.size
  summary[arm]={'loss_bits':bits,'predictions':m['native_loss']['predictions'],'all_forward_values_bitwise_equal':True,'fresh_weight_sha256':hashes[arm],'gradients':m['gradients'],'parameters_unchanged':m['parameters_unchanged'],'exported_tensors_equal':m['exported_tensors_equal']}
 assert hashes['P']==hashes['P-repeat'] and hashes['P']!=hashes['E']
 report['fixtures'][f]={'rows':item['rows'],'arms':summary,'verified_float32_values':total,'weight_identity_switch_P_E_P':True,'delta_native_bits':item['delta_native_bits'],'delta_corrected_bits':item['delta_reference_bits'],'delta_mismatch_bits':item['delta_mismatch_bits']}
write(o/'terminal.json',report)
revision={'candidateId':n,'candidateTreeSha256':job['candidate_tree_sha256'],'receipt':job['candidate_revision']}
index={'schema':'gamma.enwiki9.terminal-result-index.v1','job':ref(job_path),'guard':ref(guard_path),'arms':[],'evidence':[ref(o/'comparison.json'),ref(o/'terminal.json'),ref(o/'artifacts.json')]}
for f,item in report['fixtures'].items():
 for arm,m in item['arms'].items():
  label=f+'-'+arm;path=o/(label+'.driver.json');call=o/'numeric/calls'/label
  value={'program_id':n,'program_name':'Native forward with explicit surrogate backward','arm':label,'candidate_revision':revision,'timestamp':job['finished_at'],'run_source':job_path.relative_to(r).as_posix(),'run_purpose':'diagnostic','run_scope_label':f+'-modeled-token-rows','run_context':'Fixed P/E/P native-forward validation; exact logits/probabilities, approximate reference backward, zero optimizer updates. No codec archive or full score.','run_tags':['native-forward','fixed-checkpoint','zero-score-credit'],'data_size':None,'compressed_size':None,'roundtrip_ok':None,'determinism':None,'hutter_score':None,'scope_symbols':item['rows'],'measurement':m,'missing_diagnostics':['No exact native derivative or gradient-quality result','No updated checkpoint, final-mixer archive or full-corpus score']}
  write(path,value);index['arms'].append({'arm':label,'result':ref(path),'artifacts':{'predictions':ref(call/'predictions.f32'),'weights':ref(call/'current.weights'),'forward_receipt':ref(call/'forward.json')}})
write(o/'terminal-index.json',index)
print(json.dumps({'verified_artifacts':report['verified_artifacts'],'resources':report['resources'],'loss':{f:{a:m['loss_bits'] for a,m in v['arms'].items()} for f,v in report['fixtures'].items()}},indent=2))
