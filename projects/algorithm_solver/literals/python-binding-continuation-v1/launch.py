"""Outer process-group supervisor; use only after freeze/review approval."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time

HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists(),'refuse existing run'
    c=json.loads((HERE/'contract.json').read_text());start=time.monotonic()
    log=a.output.parent/(a.output.name+'-supervisor.log');a.output.parent.mkdir(parents=True,exist_ok=True)
    command=['taskset','-c',','.join(map(str,c['sandbox_cores'])),c['python_bin'],'-B',str(HERE/'run.py'),'--output',str(a.output)]
    env=dict(os.environ,PYTHONHASHSEED='0');timed_out=False
    with log.open('xb') as f:
        p=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        try:
            code=p.wait(timeout=c['limits']['overall_seconds']+30)
        except subprocess.TimeoutExpired:
            timed_out=True;code=None
        finally:
            # A failed worker can leave sandbox grandchildren after its parent exits.
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            p.wait()
    a.output.mkdir(parents=True,exist_ok=True)
    receipt={'elapsed':time.monotonic()-start,'exit_code':code,'outer_timeout':timed_out,'log':str(log),
             'complete':code==0 and not timed_out,'promotion_allowed':code==0 and not timed_out}
    (a.output/'supervisor-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    if not receipt['complete'] and not (a.output/'failure.json').exists():
        (a.output/'failure.json').write_text(json.dumps({'phase':'supervisor','complete':False,'promotion_allowed':False,**receipt},sort_keys=True,indent=2)+'\n')
    print(json.dumps(receipt));raise SystemExit(0 if receipt['complete'] else 1)

if __name__=='__main__':main()
