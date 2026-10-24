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
    started=time.monotonic()
    for process in processes:
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
    for process in processes:process.wait(timeout=max(.001,seconds-(time.monotonic()-started)))
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
            c.write(output/'results.json',result)
        else:
            raw=json.loads((run/'results.json').read_text())
            result=report.combine(arms,raw,contract,elapsed,run);report.publish(result,output)
        c.number(time.monotonic()-started,PHASE_SECONDS)
    except BaseException as error:
        failure={'complete':False,'validation_loaded':False,'phase':where,'exception':type(error).__name__,
                 'contract_sha256':contract_hash,'seconds':time.monotonic()-started,'partial_witnesses_promoted':False}
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        try:cleanup=stop(processes,CLEANUP_SECONDS)
        except BaseException as error:
            cleanup=CLEANUP_SECONDS;failure={'complete':False,'validation_loaded':False,
                'phase':'cleanup','exception':type(error).__name__,'contract_sha256':contract_hash,
                'seconds':time.monotonic()-started,'partial_witnesses_promoted':False}
        for log in logs:log.close()
        if writable:
            c.write(output/'supervisor.json',{'complete':failure is None,'phase':phase,'contract_sha256':contract_hash,
                'elapsed':time.monotonic()-started,'cleanup_seconds':cleanup,'returncodes':[p.returncode for p in processes]})
            if failure is not None:
                c.write(output/'failure.json',failure)
                if phase=='report':report.publish({'complete':False,'population':'fixed300_fit_only','validation_loaded':False,
                    'contract_sha256':contract_hash,'failure_sha256':c.sha(output/'failure.json'),
                    'predictions':{'P1':False,'P2':None,'P3':None}},output)
    if failure is not None:raise RuntimeError('phase incomplete; retained failure receipt')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('production','report'),required=True)
    ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--run',type=Path);a=ap.parse_args();main(a.phase,a.work,a.output,a.run)
