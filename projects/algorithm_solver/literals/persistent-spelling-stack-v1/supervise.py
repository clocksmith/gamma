"""Item54 whole-phase guard and one bounded, failure-dominant emergency path."""
import time
STARTED=time.monotonic()
import argparse
import os
from pathlib import Path
import resource
import signal
import subprocess
import common as c

CAPS={'production':3600,'report':1800};CLEANUP=10
class Timeout(BaseException):pass


def arm(deadline):
    remaining=deadline-time.monotonic()
    if remaining<=0:raise Timeout('Absolute supervisor deadline')
    signal.setitimer(signal.ITIMER_REAL,remaining)


def remove_success(out,deadline):
    for name in ('results.json','REPORT.md','supervisor-receipt.json'):
        arm(deadline)
        try:(out/name).unlink(missing_ok=True)
        except OSError:pass


def withdraw(out,phase,receipt,deadline):
    """No one-shot Timeout is swallowed; no operation starts after exhaustion."""
    remove_success(out,deadline)
    arm(deadline)
    try:out.mkdir(parents=True,exist_ok=True)
    except OSError:pass
    names=['failure.json','supervisor-receipt.json']
    if phase=='report':names.append('results.json')
    for name in names:
        arm(deadline)
        try:c.write(out/name,receipt)
        except Timeout:raise
        except Exception:
            arm(deadline)
            try:(out/name).unlink(missing_ok=True)
            except OSError:pass
    if phase=='report':
        arm(deadline)
        try:(out/'REPORT.md').write_text('# Item54 incomplete\n\nNo verdict; failure retained.\n')
        except Timeout:raise
        except Exception:
            arm(deadline)
            try:(out/'REPORT.md').unlink(missing_ok=True)
            except OSError:pass
    arm(deadline)


def kill(proc,deadline):
    if proc is not None:
        arm(deadline)
        try:os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError:pass


def cleanup(proc,log,deadline):
    first=None;kill(proc,deadline)
    if proc is not None:
        arm(deadline)
        try:proc.wait(timeout=max(.001,deadline-time.monotonic()))
        except Timeout:raise
        except Exception as error:first=error
    if log is not None:
        arm(deadline)
        try:log.close()
        except Timeout:raise
        except Exception as error:
            if first is None:first=error
    arm(deadline)
    if first is not None:raise first


def main(phase,out,run=None,record_time_best=None):
    out=Path(out);start=STARTED;deadline=start+CAPS[phase];where='preflight'
    proc=None;log=None;writable=False;digest=None;cleanup_seconds=0.0
    def expired(*_):raise Timeout('Whole phase deadline')
    signal.signal(signal.SIGALRM,expired)
    try:
        arm(deadline)
        resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2);os.sched_setaffinity(0,{0,1,2,3})
        if out.exists():
            if phase=='report':
                writable=True;archive=out/f'previous-{time.time_ns()}';archive.mkdir()
                for name in ('results.json','REPORT.md','supervisor-receipt.json','failure.json'):
                    arm(deadline)
                    if (out/name).exists():(out/name).replace(archive/name)
            raise FileExistsError('Fresh output required')
        writable=True
        config=c.read(c.HERE/'contract.json');c.verify_public(config);digest=c.hashfile(c.HERE/'contract.json')
        assert config['limits']['overall_seconds' if phase=='production' else 'report_seconds']==CAPS[phase]
        assert config['limits']['cleanup_seconds']==CLEANUP and config['limits']['address_space_bytes']==8*1024**3
        out.parent.mkdir(parents=True,exist_ok=True)
        log=(out.parent/(out.name+'-supervisor.log')).open('xb')
        target=out if phase=='production' else out/'worker-report'
        if phase=='report':
            assert run is not None and c.read(Path(run)/'supervisor-receipt.json')['complete'] is True
            assert not (Path(run)/'failure.json').exists()
        command=[config['python_bin'],'-B',str(c.HERE/('run.py' if phase=='production' else 'report.py')),'--output',str(target.resolve())]
        if phase=='report':
            command+=['--run',str(Path(run).resolve())]
            if record_time_best is not None:command+=['--record-time-best',str(Path(record_time_best).resolve())]
        where='worker';arm(deadline)
        proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
            env=dict(os.environ,PYTHONHASHSEED='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        code=proc.wait(timeout=max(.001,deadline-time.monotonic()))
        if code!=0:raise RuntimeError('Worker failed')
        where='collect';arm(deadline);result=c.read(target/'results.json');assert result['complete'] is True
        prose=(target/'REPORT.md').read_text() if phase=='report' else None
        where='cleanup';cleanup_start=time.monotonic()
        # Withdraw collected success before cleanup can exhaust its one budget.
        # The held result is republished only after successful cleanup.
        kill(proc,min(deadline,cleanup_start+CLEANUP))
        remove_success(out,min(deadline,cleanup_start+CLEANUP))
        cleanup(proc,log,min(deadline,cleanup_start+CLEANUP));log=None
        cleanup_seconds=time.monotonic()-cleanup_start
        where='publication';arm(deadline)
        receipt={'complete':True,'phase':phase,'contract_sha256':digest,'elapsed':time.monotonic()-start,
                 'cleanup_seconds':cleanup_seconds,'exit_code':proc.returncode,'outer_timeout':False,'promotion_allowed':False}
        c.write(out/'supervisor-receipt.json',receipt)
        if phase=='report':
            arm(deadline);temporary=out/'REPORT.md.pending';temporary.write_text(prose);temporary.replace(out/'REPORT.md')
        arm(deadline);c.write(out/'results.json',result)
        arm(deadline)
        return receipt
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL,0)
        emergency_start=cleanup_start if where=='cleanup' else time.monotonic()
        emergency_deadline=min(emergency_start+CLEANUP,deadline+CLEANUP)
        failure={'complete':False,'phase':where,'error_type':type(error).__name__,'promotion_allowed':False,
            'predictions':{'P1':None,'P2':None,'P3':None,'P4':None},'contract_sha256':digest,
            'elapsed':emergency_start-start,'cleanup_seconds':cleanup_seconds,
            'exit_code':None if proc is None else proc.returncode,
            'outer_timeout':type(error).__name__ in ('Timeout','TimeoutExpired','HardDeadline')}
        try:
            # Kill and withdraw first. A slow wait/close cannot leave success
            # markers behind merely because it exhausts the emergency budget.
            kill(proc,emergency_deadline)
            if writable:remove_success(out,emergency_deadline)
            cleanup(proc,log,emergency_deadline);log=None
        except BaseException as cleanup_error:
            failure['cleanup_error_type']=type(cleanup_error).__name__
        try:
            arm(emergency_deadline)
            if writable:withdraw(out,phase,failure,emergency_deadline)
        except Timeout:pass  # Stop now; never attempt another blocking operation.
        finally:signal.setitimer(signal.ITIMER_REAL,0)
        raise RuntimeError('Phase incomplete; no verdict') from error
    finally:signal.setitimer(signal.ITIMER_REAL,0)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=CAPS,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--run',type=Path);ap.add_argument('--record-time-best',type=Path)
    a=ap.parse_args();main(a.phase,a.output,a.run,a.record_time_best)
