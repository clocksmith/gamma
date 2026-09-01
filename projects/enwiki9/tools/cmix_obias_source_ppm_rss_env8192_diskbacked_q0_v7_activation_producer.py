#!/usr/bin/env python3
"""Prospective q0-only Geekbench 5 runtime-authority producer."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, platform, re, subprocess, sys
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1]
CANDIDATE_ID="cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v7"
AUTHORITY_ROOT=PROJECT/f"operations/evidence/{CANDIDATE_ID}-runtime-authority"
ACTIVATION=PROJECT/f"operations/adaptive/activations/{CANDIDATE_ID}.json"
RESULT_ROOT=PROJECT/f"results/{CANDIDATE_ID}"
SCRATCH_ROOT=PROJECT/f"scratch/{CANDIDATE_ID}"
CGROUP=Path("/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/gamma-cmix-obias-env8192-opening1m-q0-v7")
LEASE=PROJECT/"operations/runtime/exclusive_full1g.json"
LEASE_IMPL=PROJECT/"programs/gamma_managed_exclusive_lease_owned_cleanup_q0_v1/managed_exclusive_lease.py"
LEASE_VERIFY=PROJECT/"tools/managed_exclusive_lease_verify.py"
GUARD=PROJECT/"tools/run_with_resource_guard_v3.py"
GB5=Path("/usr/bin/geekbench5")

def sha(p:Path)->str:
 d=hashlib.sha256(); d.update(p.read_bytes()); return d.hexdigest()
def artifact(p:Path)->dict:
 p=p.resolve(strict=True); return {"path":str(p),"bytes":p.stat().st_size,"sha256":sha(p)}
def host()->dict:
 models=sorted({x.split(":",1)[1].strip() for x in Path('/proc/cpuinfo').read_text().splitlines() if x.lower().startswith('model name') and ':' in x})
 return {"schema":"gamma.enwiki9.cmix-runtime-host-fingerprint.v1","machine_id_sha256":hashlib.sha256(Path('/etc/machine-id').read_bytes()).hexdigest(),"uname_machine":platform.machine(),"cpu_model_names":models}
def score(p:Path)->int:
 text=p.read_bytes().decode(errors='replace')
 if not re.search(r"Geekbench\s+5(?:\.|\s|$)",text,re.I): raise RuntimeError('not Geekbench 5')
 values=[int(x.replace(',','')) for x in re.findall(r"Single[- ]Core\s+Score\s*:?\s*([0-9][0-9,]*)",text,re.I)]
 if len(values)!=1 or values[0]<=0: raise RuntimeError('ambiguous score')
 return values[0]
def load(path:Path,name:str):
 spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
def write_new(path:Path,value:dict):
 raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode(); fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600); os.write(fd,raw); os.fsync(fd); os.close(fd)

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--validation-only',action='store_true'); ap.add_argument('--cpu',type=int,required=True); a=ap.parse_args()
 if a.cpu not in os.sched_getaffinity(0): raise RuntimeError('CPU unavailable')
 os.sched_setaffinity(0,{a.cpu})
 blockers=[]
 if ACTIVATION.exists() or AUTHORITY_ROOT.exists(): blockers.append('activation/evidence namespace must be absent')
 if RESULT_ROOT.exists() or SCRATCH_ROOT.exists(): blockers.append('future gate roots must be absent')
 report={"schema":"gamma.enwiki9.cmix-obias-opening1m-q0-authority-producer-preflight.v1","candidate_id":CANDIDATE_ID,"selected_cpu":a.cpu,"affinity":sorted(os.sched_getaffinity(0)),"authority_root":str(AUTHORITY_ROOT),"activation":str(ACTIVATION),"blockers":blockers,"execution_ready":not blockers and GB5.is_file(),"claim_boundary":"q0 runtime authority only; no corpus gate."}
 if a.validation_only: print(json.dumps(report,indent=2,sort_keys=True)); return 0
 if not report['execution_ready']: raise RuntimeError('producer preflight failed')
 AUTHORITY_ROOT.mkdir(mode=0o700); work=AUTHORITY_ROOT/'scratch'; work.mkdir(mode=0o700); CGROUP.mkdir(mode=0o700)
 transition=AUTHORITY_ROOT/'lease-transition.json'; terminal=AUTHORITY_ROOT/'lease-terminal.json'; raw=AUTHORITY_ROOT/'geekbench5.txt'; guard_receipt=AUTHORITY_ROOT/'guard.json'; host_path=AUTHORITY_ROOT/'host.json'; lease_verification=AUTHORITY_ROOT/'lease-verification.json'
 lease_mod=load(LEASE_IMPL,'q0v7lease'); verifier=load(LEASE_VERIFY,'q0v7verify'); lease=None
 try:
  lease=lease_mod.ManagedExclusiveLease.acquire(lease_path=LEASE,transition_path=transition,candidate_id=CANDIDATE_ID,command_sha256=hashlib.sha256(b'geekbench5-q0-v7').hexdigest(),runner_sha256=sha(Path(__file__)),guard_path=str(GUARD),result_path=str(AUTHORITY_ROOT),scratch_path=str(work),claim_boundary='q0 Geekbench authority only')
  cmd=[sys.executable,str(GUARD),'--limit-kib','9765625','--limit-mode','tree','--official-decimal-limit-kib','9765625','--sample-interval','0.5','--cgroup-path',str(CGROUP),'--cgroup-memory-max-bytes','10000000000','--scratch-path',str(work),'--temporary-disk-limit-bytes','100000000000','--max-logical-cpus','1','--guard-json',str(guard_receipt),'--label',CANDIDATE_ID,'--phase','qualification','--',str(GB5),'--no-upload']
  with raw.open('xb') as out: subprocess.run(cmd,cwd=work,stdout=out,check=True)
 finally:
  if lease: lease.release(evidence_path=terminal)
 value,ok=verifier.verify(argparse.Namespace(transition_log=transition,terminal_lease=terminal,output=None)); write_new(lease_verification,value)
 write_new(host_path,host()); measured=score(raw)
 receipt={"schema":"gamma.enwiki9.cmix-obias-opening1m-q0-runtime-authority.v1","candidate_id":CANDIDATE_ID,"scope_bytes":1000000,"selected_cpu":a.cpu,"terminal_authority":bool(ok),"authority_root":str(AUTHORITY_ROOT),"producer":artifact(Path(__file__)),"geekbench5_single_core_score":measured,"runtime_paths":{"result_root":str(RESULT_ROOT),"scratch_root":str(SCRATCH_ROOT),"cgroup_base":str(CGROUP),"cgroup_parent_identity":{"path":str(CGROUP.parent),"inode":8608,"uid":1000,"gid":1000},"cgroup_memory_max_bytes":10000000000,"result_and_scratch_must_be_absent":True,"cgroup_base_must_be_absent":True,"result_and_scratch_must_be_distinct_disjoint_disk_backed":True},"artifacts":{"raw_geekbench5_report":artifact(raw),"host_fingerprint":artifact(host_path),"lease_transition":artifact(transition),"lease_terminal":artifact(terminal),"lease_verification":artifact(lease_verification),"guard_receipt":artifact(guard_receipt)}}
 write_new(ACTIVATION,receipt); print(json.dumps(receipt,indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
