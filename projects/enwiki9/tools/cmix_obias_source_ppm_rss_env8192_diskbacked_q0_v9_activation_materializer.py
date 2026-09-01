#!/usr/bin/env python3
"""Decision-last outer materializer for q0 v9 runtime authority."""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]; C="cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v9"; JOB_ID=C+"-runtime-authority"; PRODUCER=P/f"tools/{C}_activation_producer.py"; ROOT=P/f"operations/evidence/{C}-runtime-authority"; RECEIPT=ROOT/"producer-receipt.json"; ACTIVATION=P/f"operations/adaptive/activations/{C}.json"
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def art(p): p=Path(p).resolve(strict=True); return {"path":str(p),"bytes":p.stat().st_size,"sha256":sha(p)}
def write(p,v):
 b=(json.dumps(v,indent=2,sort_keys=True)+"\n").encode(); fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600); os.write(fd,b); os.fsync(fd); os.close(fd)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--validation-only',action='store_true');ap.add_argument('--cpu',type=int,required=True);a=ap.parse_args()
 if a.cpu not in os.sched_getaffinity(0): raise RuntimeError('CPU unavailable')
 os.sched_setaffinity(0,{a.cpu}); argv=[sys.executable,str(PRODUCER),'--cpu',str(a.cpu),'--job-id',JOB_ID]; digest=hashlib.sha256(b'\0'.join(os.fsencode(x) for x in argv)).hexdigest(); report={"schema":"gamma.enwiki9.cmix-obias-q0-v9-materializer-preflight.v1","candidate_id":C,"producer_job_id":JOB_ID,"selected_cpu":a.cpu,"affinity":sorted(os.sched_getaffinity(0)),"producer":art(PRODUCER),"argv":argv,"command_sha256":digest,"execution_ready":False,"deferred":"producer live admission and benchmark authority"}
 if a.validation_only: print(json.dumps(report,indent=2,sort_keys=True)); return 0
 if ROOT.exists() or ACTIVATION.exists(): raise RuntimeError('authority namespace occupied')
 proc=subprocess.Popen(argv,cwd=P,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True); pid=proc.pid; initial=sorted(os.sched_getaffinity(pid)); out,err=proc.communicate(); final_rc=proc.returncode
 if final_rc!=0 or initial!=[a.cpu] or not RECEIPT.is_file(): raise RuntimeError('producer lifecycle failed')
 write(ROOT/'materializer-producer.stdout',{"schema":"gamma.enwiki9.captured-stream.v1","text":out.decode(errors='replace')}); write(ROOT/'materializer-producer.stderr',{"schema":"gamma.enwiki9.captured-stream.v1","text":err.decode(errors='replace')})
 value=json.loads(RECEIPT.read_text()); producer=art(PRODUCER)
 if value.get('producer')!=producer or value.get('selected_cpu')!=a.cpu or value.get('terminal_authority') is not True: raise RuntimeError('producer decision identity mismatch')
 manifest=[art(x) for x in sorted(ROOT.rglob('*')) if x.is_file()]; paths=[x['path'] for x in manifest]
 if len(paths)!=len(set(paths)) or str(RECEIPT.resolve()) not in paths: raise RuntimeError('incomplete authority output manifest')
 activation=dict(value); activation.update({"materializer":art(__file__),"producer_receipt":art(RECEIPT),"producer_invocation":{"argv":argv,"command_sha256":digest,"pid":pid,"initial_affinity":initial,"returncode":final_rc,"exited":True},"output_manifest":{"policy":"complete-retained-authority-artifacts-v1","root":str(ROOT),"artifacts":manifest,"complete":True}})
 write(ACTIVATION,activation); print(json.dumps(activation,indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
