from pathlib import Path
import json,hashlib,sys
r=Path('projects/enwiki9').resolve();n=sys.argv[1];job_id=sys.argv[2];o=r/'results'/n
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=lambda p:{'path':p.relative_to(r).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
j=json.loads((o/'comparison.json').read_bytes());manifest=json.loads((o/'artifacts.json').read_bytes())
for a in manifest['artifacts']:
 p=r/a['path'];assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256']
job_path=next((r/'operations/adaptive/completed').glob('*'+job_id+'.json'));job=json.loads(job_path.read_bytes());guard_path=r/job['execution_resources']['guard_path'];g=json.loads(guard_path.read_bytes())
assert job['returncode']==0 and job['execution_resources']['cleanup_complete'] and g['status']=='complete' and not any(g['guards'].values())
for key in ('source_rebuild_and_repeat_exact','archive_repeat_exact','no_argument_inverse_exact','native_payload_unchanged'):assert j[key]
assert sha(o/'encode/archive9')==sha(o/'repeat/archive9')
assert j['executable_form_bytes']==(o/'comp9').stat().st_size+(o/'encode/archive9').stat().st_size
assert j['source_zip_form_bytes']==(o/'comp9.zip').stat().st_size+(o/'encode/archive9').stat().st_size
report={'schema':'gamma.enwiki9.core-delivery-terminal.v1','comparison':ref(o/'comparison.json'),'verified_artifacts':len(manifest['artifacts']),'job':ref(job_path),'guard':ref(guard_path),'package_pass':True,'qualification_complete':False,'objective_credit_bytes':0,'full_corpus_score_bytes':None,'population':j['population'],'selected_checkpoint':j['selected_checkpoint'],'executable_form_bytes':j['executable_form_bytes'],'source_zip_form_bytes':j['source_zip_form_bytes'],'gains_over_same_layout_P':j['gains_over_same_layout_P'],'resources':{'elapsed_seconds':g['elapsed_s'],'peak_cgroup_bytes':g['peaks']['cgroup_memory_peak_bytes'],'peak_scratch_allocated_bytes':g['peaks']['max_sampled_scratch_allocated_bytes'],'cleanup_complete':True,'timing_authority':'diagnostic'},'gaps':j['gaps'],'next_action':'Preserve bounded core delivery and complete-byte alternatives. No full-corpus score or submission inferred. Larger scientific gates require their own frozen population/economics; runtime qualification requires isolated calibrated admission and license closure.'}
write(o/'terminal.json',report)
rev={'candidateId':n,'candidateTreeSha256':job['candidate_tree_sha256'],'receipt':job['candidate_revision']}
index={'schema':'gamma.enwiki9.terminal-result-index.v1','job':ref(job_path),'guard':ref(guard_path),'arms':[],'evidence':[ref(o/'comparison.json'),ref(o/'terminal.json'),ref(o/'artifacts.json')]}
phases={x['phase']:x for x in j['commands']};archive=o/'encode/archive9';inverse=o/'decode/enwik9';repeat=o/'repeat/archive9'
row={'schema':'gamma.enwiki9.driver-result.v2','program_id':n,'program_name':'Complete bounded FX2 core delivery','arm':j['selected_checkpoint'],'candidate_revision':rev,'timestamp':job['finished_at'],'run_source':job_path.relative_to(r).as_posix(),'run_purpose':'diagnostic','run_scope_label':'250000-raw-core-delivery','run_context':'Complete bounded self-extracting core package with exact original native payload. Source ZIP and executable forms are alternatives; no full-enwik9 preprocessing or score claim.','run_tags':['core-delivery','restricted-inverse','zero-score-credit'],'data_size':inverse.stat().st_size,'data_sha256':sha(inverse),'compressed_size':archive.stat().st_size,'compressed_sha256':sha(archive),'roundtrip_ok':True,'determinism':{'single_host_byte_equal':True},'compress_time_s':phases['isolated-encode']['elapsed_seconds'],'decompress_time_s':phases['isolated-decode']['elapsed_seconds'],'program_size':(o/'comp9').stat().st_size,'hutter_score':None,'complete_package_bytes':None,'fixture_executable_form_bytes':j['executable_form_bytes'],'fixture_source_zip_form_bytes':j['source_zip_form_bytes'],'full_corpus_score_bytes':None,'objective_credit_bytes':0,'discovery_resource_gate_pass':True,'resource_evidence_complete':False,'score_accounting_complete':False,'qualification_status':'not-certified','prize_claimable':False,'missing_diagnostics':j['gaps'],'source_terminal':ref(o/'comparison.json')}
p=o/(j['selected_checkpoint']+'.driver.json');write(p,row);index['arms'].append({'arm':j['selected_checkpoint'],'result':ref(p),'artifacts':{'archive':ref(archive),'restored':ref(inverse),'repeat':ref(repeat),'compressor':ref(o/'comp9'),'source_zip':ref(o/'comp9.zip')}})
write(o/'terminal-index.json',index);print(json.dumps(report,indent=2))
