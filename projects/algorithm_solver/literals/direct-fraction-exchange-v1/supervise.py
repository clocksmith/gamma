"""Separate bounded production/replay phases, with group cleanup and receipts."""
import argparse
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
import common as c
import report


def stop(processes,seconds):
    started=time.monotonic();first_error=None
    for process in processes:
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        except WholeJobTimeout:raise
        except BaseException as error:
            if first_error is None:first_error=error
    for process in processes:
        remaining=seconds-(time.monotonic()-started)
        if remaining<=0:raise WholeJobTimeout('cleanup deadline')
        try:process.wait(timeout=remaining)
        except WholeJobTimeout:raise
        except BaseException as error:
            if first_error is None:first_error=error
    if first_error is not None:raise first_error
    return time.monotonic()-started


PHASE_SECONDS=1200
CLEANUP_SECONDS=10


class WholeJobTimeout(BaseException):
    pass


def main(phase,work,output,run=None):
    c.require_checks();started=time.monotonic();deadline=started+PHASE_SECONDS
    processes=[];logs=[];where='preflight';failure=None;result=None;contract=None;contract_hash=None
    writable=False
    def expired(*_):raise WholeJobTimeout('whole-phase deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,PHASE_SECONDS)
    try:
        resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2)
        os.sched_setaffinity(0,{6,7})
        if output.exists():
            if phase=='report':
                writable=True;archive=output/f'previous-{time.time_ns()}';archive.mkdir()
                for name in ('results.json','REPORT.md','supervisor.json','failure.json'):
                    if (output/name).exists():(output/name).replace(archive/name)
            raise FileExistsError('fresh phase output directory required')
        output.mkdir(parents=True);writable=True
        contract=json.loads((c.HERE/'contract.json').read_text());contract_hash=c.sha(c.HERE/'contract.json')
        assert contract['limits'][phase+'_seconds']==PHASE_SECONDS
        assert contract['limits']['cleanup_seconds']==CLEANUP_SECONDS
        assert contract['limits']['address_space_bytes']==8*1024**3
        assert contract['limits']['arm_cores']=={'R':[6],'naming':[7]}
        c.check_contract(contract,work)
        if phase=='report':assert run is not None and not (run/'failure.json').exists()
        where='workers'
        for cohort in ('R','naming'):
            log=(output/f'{cohort}.log').open('w');logs.append(log)
            command=[sys.executable,str(c.HERE/('run.py' if phase=='production' else 'report.py')),
                     '--cohort',cohort,'--work',str(work.resolve()),'--output',str(output.resolve()),'--deadline',str(deadline)]
            if phase=='report':command+=['--run',str(run.resolve())]
            processes.append(subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True))
        while True:
            codes=[p.poll() for p in processes]
            if any(code is not None and code!=0 for code in codes):raise RuntimeError('worker failure')
            if all(code==0 for code in codes):break
            if time.monotonic()>=deadline:raise WholeJobTimeout('whole-phase deadline')
            time.sleep(.05)
        where='collect'
        arms=[json.loads((output/(cohort+'/results.json' if phase=='production' else cohort+'.json')).read_text()) for cohort in ('R','naming')]
        assert all(a['complete'] is True and a['validation_loaded'] is False for a in arms)
        elapsed=c.number(time.monotonic()-started,PHASE_SECONDS)
        if phase=='production':
            result={'complete':True,'validation_loaded':False,'contract_sha256':contract_hash,'seconds':elapsed,'arms':arms}
        else:
            raw=json.loads((run/'results.json').read_text())
            result=report.combine(arms,raw,contract,elapsed,run)
        c.number(time.monotonic()-started,PHASE_SECONDS)
    except BaseException as error:
        failure={'complete':False,'validation_loaded':False,'phase':where,'exception':type(error).__name__,
                 'contract_sha256':contract_hash,'seconds':time.monotonic()-started,'partial_witnesses_promoted':False}
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        cleanup_started=time.monotonic();cleanup_error=None
        # Cleanup has its own bounded tolerance, including log flush/close.
        try:
            signal.setitimer(signal.ITIMER_REAL,CLEANUP_SECONDS)
            try:stop(processes,CLEANUP_SECONDS)
            except BaseException as error:cleanup_error=error
            for log in logs:
                remaining=CLEANUP_SECONDS-(time.monotonic()-cleanup_started)
                if remaining<=0:raise WholeJobTimeout('cleanup deadline')
                signal.setitimer(signal.ITIMER_REAL,remaining)
                try:log.close()
                except BaseException as error:
                    if cleanup_error is None:cleanup_error=error
        except BaseException as error:
            if cleanup_error is None:cleanup_error=error
        finally:
            signal.setitimer(signal.ITIMER_REAL,0)
        cleanup=time.monotonic()-cleanup_started
        if cleanup_error is not None:
            failure={'complete':False,'validation_loaded':False,'phase':'cleanup',
                'exception':type(cleanup_error).__name__,'contract_sha256':contract_hash,
                'seconds':time.monotonic()-started,'partial_witnesses_promoted':False}
    # Success is published only after worker cleanup AND every log close.
    # Receipt and publication I/O remain inside the original whole-phase cap.
    try:
        if failure is not None:raise RuntimeError('phase incomplete')
        where='publication'
        remaining=deadline-time.monotonic()
        if remaining<=0:raise WholeJobTimeout('whole-phase deadline')
        signal.setitimer(signal.ITIMER_REAL,remaining)
        c.write(output/'supervisor.json',{'complete':True,'phase':phase,'contract_sha256':contract_hash,
            'elapsed':time.monotonic()-started,'cleanup_seconds':cleanup,'returncodes':[p.returncode for p in processes]})
        if phase=='report':report.publish(result,output)
        else:c.write(output/'results.json',result)
        c.number(time.monotonic()-started,PHASE_SECONDS)
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL,0)
        if failure is None:
            failure={'complete':False,'validation_loaded':False,'phase':where,'exception':type(error).__name__,
                'contract_sha256':contract_hash,'seconds':time.monotonic()-started,'partial_witnesses_promoted':False}
        if writable:
            # Each failure write is independent: a failed receipt must never
            # bypass withdrawal of a success artifact written moments earlier.
            for name,value in [('failure.json',failure),('supervisor.json',{
                    'complete':False,'phase':phase,'contract_sha256':contract_hash,
                    'elapsed':time.monotonic()-started,'cleanup_seconds':cleanup,
                    'returncodes':[p.returncode for p in processes]})]:
                try:c.write(output/name,value)
                except BaseException:
                    try:(output/name).unlink(missing_ok=True)
                    except BaseException:pass
            try:
                if phase=='report':report.publish(report.failure_result('supervisor_failure'),output)
                else:(output/'results.json').unlink(missing_ok=True)
            except BaseException:
                # Even a broken failure publisher cannot preserve stale success.
                for name in ('results.json','REPORT.md'):
                    try:(output/name).unlink(missing_ok=True)
                    except BaseException:pass
        raise RuntimeError('phase incomplete; failure withdrawal attempted') from error
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('production','report'),required=True)
    ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--run',type=Path);a=ap.parse_args();main(a.phase,a.work,a.output,a.run)
