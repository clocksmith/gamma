"""Bounded process-group supervisor; draft contracts cannot launch."""
import os
if not __debug__ or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):
    raise RuntimeError('Assertion validation requires normal Python mode; PYTHONOPTIMIZE/-O is forbidden')

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time

HERE=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source-run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    c=json.loads((HERE/'contract.json').read_text())
    assert c['source_bound'] and c['source_run']==str(a.source_run.resolve())
    assert not a.output.exists(),'refuse existing output'
    a.output.parent.mkdir(parents=True,exist_ok=True)
    log=a.output.parent/(a.output.name+'-supervisor.log')
    command=['taskset','-c',','.join(map(str,c['all_cores'])),c['python_bin'],'-B',str(HERE/'run.py'),
             '--source-run',str(a.source_run),'--output',str(a.output)]
    start=time.monotonic()
    timeout=False
    with log.open('xb') as f:
        proc=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,
            env=dict(os.environ,PYTHONHASHSEED='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'))
        try:
            code=proc.wait(timeout=c['limits']['overall_seconds'])
        except subprocess.TimeoutExpired:
            timeout=True
            code=None
        finally:
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            proc.wait()
    a.output.mkdir(parents=True,exist_ok=True)
    receipt={'elapsed':time.monotonic()-start,'exit_code':code,'outer_timeout':timeout,
             'complete':code==0 and not timeout,'promotion_allowed':code==0 and not timeout,'log':str(log)}
    (a.output/'supervisor-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))
    raise SystemExit(0 if receipt['complete'] else 1)


if __name__=='__main__':main()
