"""Bounded metadata-only verification of native38controls/exact8 parser probe."""
import argparse,hashlib,json,pathlib

def read(p,cap=4*1024**2):
 from os import open as op,close,read as rd,O_RDONLY,O_NOFOLLOW,fstat
 import stat
 fd=op(p,O_RDONLY|O_NOFOLLOW)
 try:
  st=fstat(fd)
  if not stat.S_ISREG(st.st_mode)or st.st_size>cap:raise ValueError('bounded regular metadata required')
  chunks=[];length=0
  while True:
   block=rd(fd,min(65536,cap+1-length))
   if not block:break
   chunks.append(block);length+=len(block)
   if length>cap:raise ValueError('metadata cap')
  return b''.join(chunks)
 finally:close(fd)
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=pathlib.Path,required=True);p.add_argument('--freeze-sha256',required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();d=a.run
 sha=lambda raw:hashlib.sha256(raw).hexdigest();raw=read(d/'freeze.json')
 if sha(raw)!=a.freeze_sha256:raise ValueError('native freeze identity')
 freeze=json.loads(raw)
 for path,h in freeze['pins'].items():
  if path.endswith('inputs.private.json'):continue
  cap=128*1024**2 if path.endswith('/node')else 4*1024**2
  if sha(read(path,cap))!=h:raise ValueError('code or metadata drift')
 supraw=read(d/'native/supervisor.json');sup=json.loads(supraw);resources=json.loads(read(d/'resources.json'))
 if sup['exit_code']!=0 or not sup['no_executing_owned_processes_observed']or sup['remaining_live_owned']or sup['inspection_unreadable_pids']or sup['wall_timeout']or resources['exit_code']!=0:raise ValueError('native/cleanup incomplete')
 raw=read(d/'native/worker.log');lines=[json.loads(s)for s in raw.splitlines()];tests=lines[0]['controls'];rows=lines[1:-1]
 if len(tests)!=38 or len({t['name']for t in tests})!=38 or any(t['expected']!=t['observed']for t in tests):raise ValueError('controls incomplete')
 if lines[-1]!={'done':8,'source_bytes':1053,'candidate_execution':False,'transformed_sources':0,'qualification':False}:raise ValueError('terminal incomplete')
 auditpath=next(path for path in freeze['pins']if path.endswith('/finite-case-audit.json'));audit=json.loads(read(auditpath));expected={str(r['problem_id'])+':original':r for r in audit['rows']}
 if len(rows)!=8 or {r['key']for r in rows}!=set(expected)or sum(r['source_bytes']for r in rows)!=1053:raise ValueError('exact8 mismatch')
 for r in rows:
  if r['source_sha256']!=expected[r['key']]['source_sha256']or r['admitted']is not False:raise ValueError('source/admission drift')
 result={'schema':'gamma.extrema8.native-parser-verification.v3','verified':True,'freeze_sha256':a.freeze_sha256,'raw_metadata_sha256':sha(raw),'supervisor_sha256':sha(supraw),'controls':tests,'source_results':rows,'sources':8,'source_bytes':1053,'finite_bound_cases':sum(r['cases']for r in audit['rows']),'syntactic_candidates':sum(r['syntactic_candidate']for r in rows),'candidate_execution':False,'transformed_sources':0,'qualified':0,'cleanup_passed':True,'resources':resources,'independent_source_domain_review_still_required':True,'runtime_intrinsic_attestation_still_required':True,'M1':'UNMET'}
 a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in('controls','source_results','resources')}))
if __name__=='__main__':main()
