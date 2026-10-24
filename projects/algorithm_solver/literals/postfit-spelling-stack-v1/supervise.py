"""Separate whole production/replay caps; bounded group cleanup and fail-closed publication."""
import argparse
import os
from pathlib import Path
import resource
import signal
import subprocess
import time
import common as c

CAPS={'production':3600,'report':1800};CLEANUP=10
class Timeout(BaseException):pass


def withdraw(out,phase,receipt):
    """Failure receipt I/O never skips independent success withdrawal."""
    try:out.mkdir(parents=True,exist_ok=True)
    except BaseException:pass
    for name,value in [('failure.json',receipt),('supervisor-receipt.json',receipt)]:
        try:c.write(out/name,value)
        except BaseException:
            try:(out/name).unlink(missing_ok=True)
            except BaseException:pass
    failed={'complete':False,'promotion_allowed':False,'predictions':{'P1':None,'P2':None,'P3':None,'P4':None},'failure_reason':'supervisor_failure'}
    for name in ('results.json','REPORT.md'):
        path=out/name
        try:
            if phase=='production':path.unlink(missing_ok=True)
            elif name=='results.json':c.write(path,failed)
            else:path.write_text('# Item46 incomplete\n\nNo verdict; failure retained.\n')
        except BaseException:
            try:path.unlink(missing_ok=True)
            except BaseException:pass


def cleanup(proc,log,seconds):
    started=time.monotonic();first=None
    if proc is not None:
        try:os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        except Timeout:raise
        except BaseException as error:first=error
        remaining=seconds-(time.monotonic()-started)
        if remaining<=0:raise Timeout('cleanup deadline')
        try:proc.wait(timeout=remaining)
        except Timeout:raise
        except BaseException as error:
            if first is None:first=error
    if log is not None:
        remaining=seconds-(time.monotonic()-started)
        if remaining<=0:raise Timeout('cleanup deadline')
        signal.setitimer(signal.ITIMER_REAL,remaining)
        try:log.close()
        except Timeout:raise
        except BaseException as error:
            if first is None:first=error
    if first is not None:raise first


def main(phase,out,run=None,record_time_best=None):
    out=Path(out);start=time.monotonic();deadline=start+CAPS[phase];where='preflight';proc=None;log=None;failure=None
    writable=False;digest=None;config=None;result=None;prose=None
    def expired(*_):raise Timeout('whole phase deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,CAPS[phase])
    try:
        resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2);os.sched_setaffinity(0,{0,1,2,3})
        if out.exists():
            if phase=='report':
                writable=True;archive=out/f'previous-{time.time_ns()}';archive.mkdir()
                for name in ('results.json','REPORT.md','supervisor-receipt.json','failure.json'):
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
        where='worker'
        proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
            env=dict(os.environ,PYTHONHASHSEED='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        code=proc.wait(timeout=max(.001,deadline-time.monotonic()))
        if code!=0:raise RuntimeError('Worker failed')
        where='collect';result=c.read(target/'results.json');assert result['complete'] is True
        if phase=='report':prose=(target/'REPORT.md').read_text()
    except BaseException as error:
        failure={'complete':False,'phase':where,'error_type':type(error).__name__,'promotion_allowed':False}
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);cleanup_start=time.monotonic()
        try:
            signal.setitimer(signal.ITIMER_REAL,CLEANUP)
            cleanup(proc,log,CLEANUP)
        except BaseException as error:
            failure={'complete':False,'phase':'cleanup','error_type':type(error).__name__,'promotion_allowed':False}
        finally:signal.setitimer(signal.ITIMER_REAL,0)
        cleanup_seconds=time.monotonic()-cleanup_start
    try:
        if failure is not None:raise RuntimeError('Phase incomplete')
        where='publication';remaining=deadline-time.monotonic()
        if remaining<=0:raise Timeout('whole phase deadline')
        signal.setitimer(signal.ITIMER_REAL,remaining)
        receipt={'complete':True,'phase':phase,'contract_sha256':digest,'elapsed':time.monotonic()-start,
                 'cleanup_seconds':cleanup_seconds,'exit_code':proc.returncode,'outer_timeout':False,'promotion_allowed':False}
        c.write(out/'supervisor-receipt.json',receipt)
        if phase=='report':
            temporary=out/'REPORT.md.pending';temporary.write_text(prose);temporary.replace(out/'REPORT.md')
            c.write(out/'results.json',result)
        if time.monotonic()>deadline:raise Timeout('whole phase deadline')
        return receipt
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL,0)
        if failure is None:failure={'complete':False,'phase':where,'error_type':type(error).__name__,'promotion_allowed':False}
        failure.update(contract_sha256=digest,elapsed=time.monotonic()-start,cleanup_seconds=cleanup_seconds,
                       exit_code=None if proc is None else proc.returncode,outer_timeout=failure['error_type'] in ('Timeout','TimeoutExpired','HardDeadline'))
        if writable:withdraw(out,phase,failure)
        raise RuntimeError('Phase incomplete; no verdict') from error
    finally:signal.setitimer(signal.ITIMER_REAL,0)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=CAPS,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--run',type=Path);ap.add_argument('--record-time-best',type=Path)
    a=ap.parse_args();main(a.phase,a.output,a.run,a.record_time_best)
