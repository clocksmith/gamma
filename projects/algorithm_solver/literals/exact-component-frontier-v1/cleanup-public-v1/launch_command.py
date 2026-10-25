"""Reusable owned-session wrapper. Review exact command separately before launch.
Does not authorize execution or replace qualification's own report verifier.
"""
import argparse,json,os,signal,time
from pathlib import Path
from supervise import supervise
if __name__=='__main__':
 start=time.monotonic();os.umask(0o077);state={'signals':[]}
 def handler(signum,frame):state['signals'].append(signum)
 for signum in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):signal.signal(signum,handler)
 p=argparse.ArgumentParser();p.add_argument('--wall-seconds',type=int,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
 if not 1<=a.wall_seconds<=900:p.error('bounded wall must be1..900')
 command=a.command[1:] if a.command and a.command[0]=='--' else a.command
 if not command:p.error('explicit independently reviewed child command required')
 a.output.mkdir(mode=0o700,parents=True,exist_ok=False)
 result=supervise(command,a.output/'worker.log',start+a.wall_seconds,state)
 result.update(wall_seconds=time.monotonic()-start,absolute_deadline_monotonic=start+a.wall_seconds,wall_budget_seconds=a.wall_seconds,command=command,qualification=False)
 good=result['exit_code']==0 and not result['wall_timeout'] and not result['error_type'] and not result['termination_signals'] and result['no_executing_owned_processes_observed']
 result['status']='completed_child_requires_independent_verification' if good else 'failed'
 (a.output/'supervisor.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 raise SystemExit(0 if good else 1)
