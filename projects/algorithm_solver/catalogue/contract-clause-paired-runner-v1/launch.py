"""Exact permitted phase launcher, reviewed owned-tree RSS supervisor reused."""
import argparse,json,os,signal,time
from pathlib import Path
from owner import verified,module,sha,HERE,BASE

def launch(a):
 start=time.monotonic();f=verified(dict(path=a.freeze,sha256=a.freeze_sha256));out=Path(a.output);out.mkdir(exist_ok=False);state={'signals':[]};old={};evidence=None;error=None
 def handler(n,frame):state['signals'].append(n)
 try:
  for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):old[sig]=signal.signal(sig,handler)
  if sha(Path(f['python']).resolve().read_bytes())!=f['native_python_sha256']:raise ValueError('native Python identity')
  owned=module('owned_supervisor',BASE/'integrated-recognition-policy-v1/owned_supervisor.py');env=dict(os.environ,PYTHONPATH=str(BASE.parents[2]),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
  argv=[f['python'],str(HERE/'run.py'),'--phase',a.phase,'--freeze',a.freeze,'--freeze-sha256',a.freeze_sha256,'--authorization',a.authorization,'--authorization-sha256',a.authorization_sha256,'--output',str(out/'results')]
  evidence=owned.supervise(argv,out/'native.log',start+f['resources']['wall_seconds'],state,grace=0,rss_limit_bytes=f['resources']['owned_rss_limit_bytes'],env=env,cwd=BASE.parents[2])
 except BaseException as exc:error=type(exc).__name__
 finally:
  for sig,previous in old.items():signal.signal(sig,previous)
 passed=evidence is not None and evidence['exit_code']==0 and not evidence['wall_timeout']and not evidence['error_type']and not evidence['termination_signals']and not evidence['rss_limit_exceeded']and evidence['no_executing_owned_processes_observed']
 if passed:
  try:
   r=json.loads((out/'results/report.json').read_text());passed=r['status']=='completed'and r['phase']==a.phase and r['freeze_sha256']==a.freeze_sha256
  except (OSError,ValueError,KeyError):passed=False
 summary=dict(status='completed'if passed and error is None else'failed',phase=a.phase,freeze_sha256=a.freeze_sha256,error_type=error,owned_tree=evidence,wall_seconds=time.monotonic()-start,recognition_qualified=False,confirmation_read=False);(out/'supervisor.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
 if summary['status']=='failed':(out/'failure.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
 return 0 if summary['status']=='completed'else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('cache','replay'),required=True)
 for n in ('freeze','freeze-sha256','authorization','authorization-sha256','output'):p.add_argument('--'+n,required=True)
 raise SystemExit(launch(p.parse_args()))
