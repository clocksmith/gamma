"""Fresh group, whole-clock budget, and bounded failure-dominant publication."""
import time
STARTED=time.monotonic()
import signal
class BootstrapDeadline(BaseException):pass
if __name__=='__main__':
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(BootstrapDeadline('Import deadline')))
    signal.setitimer(signal.ITIMER_REAL,max(.000001,STARTED+1200-time.monotonic()))
import argparse
import os
from pathlib import Path
import resource
import signal
import subprocess
import common as c
import run as worker

Deadline=worker.Deadline;arm=worker.arm

def kill(proc,deadline):
    if proc is not None:
        arm(deadline)
        try:os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError:pass

def cleanup(proc,log,deadline):
    kill(proc,deadline)
    if proc is not None:
        arm(deadline);proc.wait(timeout=max(.001,deadline-time.monotonic()))
    if log is not None:arm(deadline);log.close()
    arm(deadline)

def main(out):
    out=Path(out);deadline=STARTED+c.WHOLE_SECONDS;proc=None;log=None;writable=False;where='preflight';cleanup_start=None
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(Deadline('Supervisor deadline')))
    try:
        arm(deadline);resource.setrlimit(resource.RLIMIT_AS,(c.MEMORY,)*2);os.sched_setaffinity(0,{0,1,2,3})
        assert not out.exists(),'Fresh output required';writable=True
        config=c.read(c.HERE/'contract.json');c.verify(config);out.mkdir(parents=True)
        arm(deadline);log=(out/'worker.log').open('xb')
        command=[config['python_bin'],'-B',str(c.HERE/'run.py'),'--output',str((out/'worker').resolve())]
        where='worker';proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
          env=dict(os.environ,PYTHONHASHSEED='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        arm(deadline);code=proc.wait(timeout=max(.001,deadline-time.monotonic()));assert code==0
        where='collect';arm(deadline);value=c.read(out/'worker/results.json')
        worker.validate_output(value)
        assert value['contract_sha256']==c.hashfile(c.HERE/'contract.json')
        assert value['worker_seconds']<=c.WORKER_SECONDS and not (out/'worker/failure.json').exists()
        arm(deadline);text=(out/'worker/REPORT.md').read_text()
        where='cleanup';cleanup_start=time.monotonic();end=min(deadline,cleanup_start+c.CLEANUP)
        kill(proc,end);worker.remove_success(out,end);cleanup(proc,log,end);log=None
        where='publication';arm(deadline)
        receipt={'complete':True,'contract_sha256':value['contract_sha256'],'elapsed':time.monotonic()-STARTED,
          'cleanup_seconds':time.monotonic()-cleanup_start,'exit_code':code,'outer_timeout':False,'historical_only':True,'promotion_allowed':False}
        assert value['worker_seconds']<=receipt['elapsed']<=c.WHOLE_SECONDS
        c.write(out/'supervisor.json',receipt);arm(deadline);(out/'REPORT.md').write_text(text)
        arm(deadline);c.write(out/'results.json',value);arm(deadline);return receipt
    except BaseException as error:
        start=cleanup_start if where=='cleanup' else time.monotonic()
        end=min(start+c.CLEANUP,deadline+c.CLEANUP,getattr(error,'_carrier58_failure_deadline',float('inf')))
        error._carrier58_failure_deadline=end
        try:
            kill(proc,end)
            if writable:worker.remove_success(out,end)
            cleanup(proc,log,end);log=None
        except BaseException:pass # Next operation must rearm the SAME end.
        try:
            arm(end)
            if writable:worker.withdraw(out,error,deadline)
        except Deadline:pass
        raise RuntimeError('Item58 incomplete; no historical verdict') from error
    finally:signal.setitimer(signal.ITIMER_REAL,0)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();main(a.output)
