#!/usr/bin/env python3
"""Prospective stdlib-only owned-cgroup Geekbench 5 q0 authority producer."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,platform,re,secrets,shutil,subprocess,time
from pathlib import Path
P=Path(__file__).resolve().parents[1]; C="cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v8"
A=P/f"operations/evidence/{C}-runtime-authority"; ACT=P/f"operations/adaptive/activations/{C}.json"; R=P/f"results/{C}"; S=P/f"scratch/{C}"
PARENT=Path("/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice"); FUTURE=PARENT/"gamma-cmix-obias-env8192-opening1m-q0-v8"
LEASE=P/"operations/runtime/exclusive_full1g.json"; LOCK=LEASE.with_name(LEASE.name+".lock"); LI=P/"programs/gamma_managed_exclusive_lease_owned_cleanup_q0_v1/managed_exclusive_lease.py"; LV=P/"tools/managed_exclusive_lease_verify.py"; RUNNING=P/"operations/adaptive/running"; GB=Path("/usr/bin/geekbench5")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def art(p): p=Path(p).resolve(strict=True); return {"path":str(p),"bytes":p.stat().st_size,"sha256":sha(p)}
def write(p,v):
 b=(json.dumps(v,indent=2,sort_keys=True)+"\n").encode(); fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600); os.write(fd,b); os.fsync(fd); os.close(fd)
def module(p,n): q=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(q); q.loader.exec_module(m); return m
def host():
 models=sorted({x.split(':',1)[1].strip() for x in Path('/proc/cpuinfo').read_text().splitlines() if x.lower().startswith('model name') and ':' in x}); return {"schema":"gamma.enwiki9.cmix-runtime-host-fingerprint.v1","machine_id_sha256":hashlib.sha256(Path('/etc/machine-id').read_bytes()).hexdigest(),"uname_machine":platform.machine(),"cpu_model_names":models}
def ints(p):
 out={};
 for line in p.read_text().splitlines():
  k,v=line.split(); out[k]=int(v)
 return out
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--validation-only',action='store_true'); ap.add_argument('--cpu',type=int,required=True); a=ap.parse_args(); allowed=os.sched_getaffinity(0)
 if a.cpu not in allowed: raise RuntimeError('selected CPU unavailable')
 os.sched_setaffinity(0,{a.cpu}); blockers=[]
 for p in (A,ACT,R,S,FUTURE):
  if p.exists() or p.is_symlink(): blockers.append(f'namespace occupied:{p}')
 report={"schema":"gamma.enwiki9.cmix-obias-opening1m-q0-authority-producer-preflight.v2","candidate_id":C,"selected_cpu":a.cpu,"affinity":sorted(os.sched_getaffinity(0)),"deferred_live_checks":["adaptive-running-empty","canonical-lease-empty","delegated-parent-identity-controllers-writable-empty","Geekbench-executable-identity","owned-cgroup-lifecycle"],"blockers":blockers,"execution_ready":False}
 if a.validation_only: print(json.dumps(report,indent=2,sort_keys=True)); return 0
 if blockers or any(RUNNING.glob('*.json')) or LEASE.exists() or LOCK.exists(): raise RuntimeError('exclusive admission failed')
 st=PARENT.stat(); controllers=set((PARENT/'cgroup.controllers').read_text().split()); direct=(PARENT/'cgroup.procs').read_text().split()
 if {"memory","pids"}-controllers or direct or not os.access(PARENT,os.W_OK) or (st.st_ino,st.st_uid,st.st_gid)!=(8608,1000,1000): raise RuntimeError('delegated parent contract failed')
 executable=art(GB); argv=[str(GB.resolve(strict=True)),"--no-upload"]; command_sha=hashlib.sha256(b'\0'.join(os.fsencode(x) for x in argv)).hexdigest()
 child=None; inode=None; lease=None; samples=[]; joined=False; released=False; proc=None; rc=None; residue=False; same=False; empty_cleanup=False; ready_r=ready_w=release_r=release_w=None
 try:
  A.mkdir(mode=0o700); work=A/'scratch'; work.mkdir(mode=0o700); transition=A/'lease-transition.json'; terminal=A/'lease-terminal.json'; verified=A/'lease-verification.json'; stdout=A/'geekbench5.stdout'; stderr=A/'geekbench5.stderr'; hostp=A/'host.json'; lm=module(LI,'v8lease'); vm=module(LV,'v8verify')
  lease=lm.ManagedExclusiveLease.acquire(lease_path=LEASE,transition_path=transition,candidate_id=C,command_sha256=command_sha,runner_sha256=sha(__file__),guard_path=str(Path(__file__).resolve()),result_path=str(A),scratch_path=str(work),claim_boundary='q0 Geekbench runtime authority only')
  if any(RUNNING.glob('*.json')) or R.exists() or S.exists() or FUTURE.exists(): raise RuntimeError('admission changed after lease acquisition')
  child=PARENT/f"gamma-q0-v8-gb-{secrets.token_hex(16)}"; child.mkdir(mode=0o700); inode=child.stat().st_ino; (child/'memory.max').write_text('10000000000'); (child/'memory.swap.max').write_text('0'); memory_max=int((child/'memory.max').read_text()); swap_max=int((child/'memory.swap.max').read_text()); empty=(child/'cgroup.procs').read_text().split()==[]; events_before=ints(child/'memory.events')
  ready_r,ready_w=os.pipe(); release_r,release_w=os.pipe(); join="import os;open(%r,'w').write(str(os.getpid()));os.write(%d,b'1');os.read(%d,1);os.execv(%r,%r)"%(str(child/'cgroup.procs'),ready_w,release_r,argv[0],argv)
  launch_argv=[os.sys.executable,'-c',join]; launch_digest=hashlib.sha256(b'\0'.join(os.fsencode(x) for x in launch_argv)).hexdigest(); python_executable=art(os.sys.executable)
  with stdout.open('xb') as out,stderr.open('xb') as err: proc=subprocess.Popen(launch_argv,stdout=out,stderr=err,start_new_session=True,pass_fds=(ready_w,release_r))
  os.close(ready_w); ready_w=None; os.close(release_r); release_r=None; joined=os.read(ready_r,1)==b'1' and str(proc.pid) in (child/'cgroup.procs').read_text().split()
  if not joined: raise RuntimeError('child did not join before monitored execution')
  os.write(release_w,b'1'); released=True; os.close(release_w); release_w=None
  while proc.poll() is None:
   pids=[int(x) for x in (child/'cgroup.procs').read_text().split()]; samples.append({"pids":pids,"affinities":{str(pid):sorted(os.sched_getaffinity(pid)) for pid in pids},"allowed_cpus":sorted({cpu for pid in pids for cpu in os.sched_getaffinity(pid)}),"memory_current":int((child/'memory.current').read_text()),"memory_peak":int((child/'memory.peak').read_text())}); lease.heartbeat(); time.sleep(.5)
  rc=proc.wait()
 finally:
  for fd in (ready_r,ready_w,release_r,release_w):
   if fd is not None:
    try: os.close(fd)
    except OSError: pass
  if proc is not None and proc.poll() is None:
   try: os.killpg(proc.pid,15); proc.wait(timeout=10)
   except Exception:
    if child is not None and (child/'cgroup.kill').exists(): (child/'cgroup.kill').write_text('1')
    proc.wait()
  if child is not None and child.exists():
   for _ in range(100):
    if not (child/'cgroup.procs').read_text().split(): break
    time.sleep(.01)
   events_after=ints(child/'memory.events'); final_peak=int((child/'memory.peak').read_text()); empty_cleanup=(child/'cgroup.procs').read_text().split()==[]; same=child.name.startswith('gamma-q0-v8-gb-') and child.stat().st_ino==inode
   if empty_cleanup and same: child.rmdir(); residue=not child.exists()
  if lease: lease.release(evidence_path=terminal)
 value,ok=vm.verify(argparse.Namespace(transition_log=transition,terminal_lease=terminal,output=None)); write(verified,value); write(hostp,host()); events={k:events_after.get(k,0)-events_before.get(k,0) for k in set(events_before)|set(events_after)}; disk=sum(x.stat().st_size for x in work.rglob('*') if x.is_file())
 launcher={"returncode":rc,"selected_cpu":a.cpu,"child_allowed_cpus":samples[-1]['allowed_cpus'],"python_executable":python_executable,"launch_argv":launch_argv,"launch_command_sha256":launch_digest,"owned_cgroup":str(child),"owned_inode":inode,"memory_max_bytes":memory_max,"memory_swap_max_bytes":swap_max,"empty_before_spawn":empty,"joined_before_exec":joined,"release_after_join":released,"samples":samples,"final_memory_peak":final_peak,"memory_events_before":events_before,"memory_events_after":events_after,"memory_events":events,"scratch_disk_bytes":disk,"same_inode_cleanup":same,"empty_before_cleanup":empty_cleanup,"residue_absent":residue,"parent":{"path":str(PARENT),"inode":st.st_ino,"uid":st.st_uid,"gid":st.st_gid,"controllers":sorted(controllers),"direct_procs_empty":not direct}}
 if not(ok and rc==0 and memory_max==10000000000 and swap_max==0 and samples and all(x['allowed_cpus']==[a.cpu] for x in samples) and events.get('oom',0)==events.get('oom_kill',0)==events.get('max',0)==0 and same and residue): raise RuntimeError('terminal authority predicates failed')
 receipt={"schema":"gamma.enwiki9.cmix-obias-opening1m-q0-runtime-authority.v2","candidate_id":C,"scope_bytes":1000000,"selected_cpu":a.cpu,"terminal_authority":True,"authority_root":str(A),"producer":art(__file__),"geekbench5_executable":executable,"argv":argv,"command_sha256":command_sha,"geekbench5_single_core_score":int(re.findall(r'Single[- ]Core\s+Score\s*:?\s*([0-9][0-9,]*)',stdout.read_text(errors='replace'),re.I)[0].replace(',','')),"runtime_paths":{"result_root":str(R),"scratch_root":str(S),"cgroup_base":str(FUTURE),"cgroup_parent_identity":{"path":str(PARENT),"inode":8608,"uid":1000,"gid":1000},"cgroup_memory_max_bytes":10000000000,"result_and_scratch_must_be_absent":True,"cgroup_base_must_be_absent":True,"result_and_scratch_must_be_distinct_disjoint_disk_backed":True},"launcher":launcher,"artifacts":{"raw_geekbench5_report":art(stdout),"raw_stderr":art(stderr),"host_fingerprint":art(hostp),"lease_transition":art(transition),"lease_terminal":art(terminal),"lease_verification":art(verified)}}
 write(ACT,receipt); print(json.dumps(receipt,indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
