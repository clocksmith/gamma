from pathlib import Path
import json,hashlib,socket
r=Path('projects/enwiki9').resolve();n='fx2_matched_train250k_q0_v1';o=r/'results'/n
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=lambda p:{'path':p.relative_to(r).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
j=json.loads((o/'comparison.json').read_bytes());manifest=json.loads((o/'artifacts.json').read_bytes());plan=json.loads((r/f'operations/provenance/{n}_plan.json').read_bytes())
for a in manifest['artifacts']:
 p=r/a['path'];assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256']
job_path=next((r/'operations/adaptive/completed').glob('*20260920T031533Z_600d9d3b8d.json'));job=json.loads(job_path.read_bytes());guard_path=r/job['execution_resources']['guard_path'];g=json.loads(guard_path.read_bytes())
assert job['returncode']==0 and job['execution_resources']['cleanup_complete'] and g['status']=='complete' and not any(g['guards'].values())
report={'schema':'gamma.enwiki9.matched-training-terminal.v1','comparison':ref(o/'comparison.json'),'verified_artifacts':len(manifest['artifacts']),'job':ref(job_path),'guard':ref(guard_path),'selected':j['selected'],'confirmation_component_gain':j['confirmation_component_gain'],'confirmation_payload_gain':j['confirmation_payload_gain'],'scale_ready':j['scale_ready'],'paying_descendant':j['paying_descendant'],'objective_credit_bytes':0,'full_corpus_score_bytes':None,'resources':{'elapsed_seconds':g['elapsed_s'],'peak_cgroup_bytes':g['peaks']['cgroup_memory_peak_bytes'],'peak_scratch_allocated_bytes':g['peaks']['max_sampled_scratch_allocated_bytes'],'cleanup_complete':True,'timing_authority':'diagnostic'},'candidate_interface_audit':{'valid':False,'missing':'Explicit codec reference in experiment_recipe candidate.json. Frozen experiment independently binds exact native source ZIP, model checkpoints, inputs and entrypoint.','effect':'No new admission under this incomplete manifest. Preserve original measured bytes; descendant must declare the actual native codec/model identities. This is separate from numerical/inverse validity.'},'next_action':'Price selected component in the complete core package. Do not scale this training profile if payload gain is nonpositive. Preserve P and all descendants; no metadata or budget increase.'}
write(o/'terminal.json',report)
rev={'candidateId':n,'candidateTreeSha256':job['candidate_tree_sha256'],'receipt':job['candidate_revision']}
index={'schema':'gamma.enwiki9.terminal-result-index.v1','job':ref(job_path),'guard':ref(guard_path),'arms':[],'evidence':[ref(o/'comparison.json'),ref(o/'terminal.json'),ref(o/'artifacts.json'),ref(o/'selection.json')]}
phases={x['phase']:x for x in j['commands']}
for population,arms in j['measurements'].items():
 for arm,m in arms.items():
  label=population+'-'+arm;raw=r/plan['populations'][population]['raw'];archive=o/'native'/(label+'.arc');inverse=o/'native'/(label+'.raw');repeat=o/'native'/(label+'.repeat.arc')
  assert sha(raw)==sha(inverse) and sha(archive)==sha(repeat)
  enc=phases[label+'-encode'];dec=phases[label+'-decode']
  row={'schema':'gamma.enwiki9.driver-result.v2','program_id':n,'program_name':'Matched native-forward data and weight objectives','arm':label,'candidate_revision':rev,'timestamp':job['finished_at'],'run_source':job_path.relative_to(r).as_posix(),'run_purpose':'diagnostic','run_scope_label':label,'run_context':'Fresh native archive under fixed matched training plan; approximate backward and actual packed files. No complete delivery or full-corpus score.','run_tags':['native-forward','matched-training','zero-score-credit'],'data_path':raw.relative_to(r).as_posix(),'data_size':raw.stat().st_size,'data_sha256':sha(raw),'compressed_size':archive.stat().st_size,'compressed_sha256':sha(archive),'compressed_md5':hashlib.md5(archive.read_bytes()).hexdigest(),'bits_per_byte':8*archive.stat().st_size/raw.stat().st_size,'roundtrip_ok':True,'determinism':{'single_host_byte_equal':True},'compress_time_s':enc['elapsed_seconds'],'decompress_time_s':dec['elapsed_seconds'],'memory_kib':{'peak':enc['rusage']['maximum_process_rss_kib']},'memory_scope':'GNU time maximum process RSS; aggregate job cgroup bound separately','packed_model_bytes':m['packed_bytes'],'planning_model_copies':2,'program_size':None,'hutter_score':None,'complete_package_bytes':None,'full_corpus_score_bytes':None,'objective_credit_bytes':0,'discovery_resource_gate_pass':True,'resource_evidence_complete':False,'score_accounting_complete':False,'qualification_status':'not-certified','prize_claimable':False,'source_terminal':ref(o/'comparison.json'),'host':{'hostname':socket.gethostname()},'missing_diagnostics':['Full-corpus package and isolated calibration unavailable','Original recipe manifest lacks codec reference; experiment native inputs remain exact; no renewed admission']}
  path=o/(label+'.driver.json');write(path,row);index['arms'].append({'arm':label,'result':ref(path),'artifacts':{'archive':ref(archive),'restored':ref(inverse),'repeat':ref(repeat)}})
write(o/'terminal-index.json',index)
print(json.dumps(report,indent=2))
