"""One bounded process-group supervisor; requires the reviewed activated contract."""
import argparse
import json
import os
from pathlib import Path
import signal
import resource
import subprocess
import time
from common import HERE,contract,sha,write,require_assertions

def main():
    require_assertions()
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    assert not args.output.exists(),'refuse existing run; no retries/resume'
    c=contract();started=time.monotonic();args.output.parent.mkdir(parents=True,exist_ok=True)
    resource.setrlimit(resource.RLIMIT_AS,(c['limits']['address_space_bytes'],)*2)
    log=args.output.parent/(args.output.name+'-supervisor.log');timeout=False
    env=dict(os.environ,PYTHONHASHSEED='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    command=['taskset','-c',','.join(map(str,c['cores'])),c['python_bin'],'-B',str(HERE/'run.py'),'--output',str(args.output.resolve())]
    with log.open('xb') as stream:
        process=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        try:code=process.wait(timeout=c['overall_seconds']+30)
        except subprocess.TimeoutExpired:timeout=True;code=None
        finally:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            process.wait()
    args.output.mkdir(parents=True,exist_ok=True)
    receipt={'elapsed':time.monotonic()-started,'exit_code':code,'outer_timeout':timeout,
        'complete':code==0 and not timeout,'contract_sha256':sha((HERE/'contract.json').read_bytes())}
    write(args.output/'supervisor-receipt.json',receipt)
    if not receipt['complete'] and not (args.output/'failure.json').exists():
        write(args.output/'failure.json',{'phase':'supervisor','complete':False,'promotion_allowed':False})
    print(json.dumps(receipt));raise SystemExit(0 if receipt['complete'] else 1)
if __name__=='__main__':main()
