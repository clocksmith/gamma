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


def main(phase,work,output,run=None):
    c.mechanism.parent.require_checks();started=time.monotonic();processes=[];logs=[]
    contract=json.loads((c.HERE/'contract.json').read_text());limit=contract['limits'][phase+'_seconds']
    deadline=started+limit;where='preflight';failure=None;result=None
    if output.exists():
        if phase=='report':
            # A refused rerun must not leave an old success beside the new
            # failure. Preserve that success before publishing no verdict.
            archive=output/f'previous-{time.time_ns()}';archive.mkdir()
            for name in ('results.json','REPORT.md'):
                if (output/name).exists():(output/name).replace(archive/name)
            report.publish({'complete':False,'population':'fixed300_fit_only','validation_loaded':False,
                'failure_reason':'fresh_output_directory_required','predictions':{'P1':False,'P2':None,'P3':None}},output)
        raise FileExistsError('fresh phase output directory required')
    output.mkdir(parents=True,exist_ok=False)
    def expired(*_):raise TimeoutError('whole-phase deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,limit)
    try:
        resource.setrlimit(resource.RLIMIT_AS,(contract['limits']['address_space_bytes'],)*2)
        os.sched_setaffinity(0,{core for cores in contract['limits']['arm_cores'].values() for core in cores})
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
            if time.monotonic()>=deadline:raise TimeoutError('whole-phase deadline')
            time.sleep(.05)
        where='collect'
        arms=[json.loads((output/(cohort+'/results.json' if phase=='production' else cohort+'.json')).read_text()) for cohort in ('R','naming')]
        assert all(a['complete'] is True and a['validation_loaded'] is False for a in arms)
        elapsed=c.number(time.monotonic()-started,limit)
        if phase=='production':
            result={'complete':True,'validation_loaded':False,'contract_sha256':c.sha(c.HERE/'contract.json'),'seconds':elapsed,'arms':arms}
            c.write(output/'results.json',result)
        else:
            raw=json.loads((run/'results.json').read_text());report.verify_run(raw,contract)
            assert all(c.number(a['replay_seconds'],elapsed)>=0 for a in arms)
            p2=all(a['points'][3]['joint_path_increase'] is not None and a['points'][3]['joint_path_increase']>0 for a in arms)
            p3=any(p['joint_integer_lower_bound'] is not None and p['joint_integer_lower_bound']>0 for a in arms for p in a['points'])
            result={'schema':'gamma.joint-quantile-fraction.report.v1','complete':True,'validation_loaded':False,
                    'population':'fixed300_fit_only','contract_sha256':c.sha(c.HERE/'contract.json'),
                    'private_results_sha256':c.sha(run/'results.json'),'production_seconds':raw['seconds'],
                    'replay_seconds':elapsed,'arms':arms,'predictions':{'P1':True,'P2':p2,'P3':p3}}
            report.publish(result,output)
        c.number(time.monotonic()-started,limit)
    except BaseException as error:
        failure={'complete':False,'validation_loaded':False,'phase':where,'exception':type(error).__name__,
                 'contract_sha256':c.sha(c.HERE/'contract.json'),'seconds':time.monotonic()-started,'partial_certificates_promoted':False}
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        try:cleanup=stop(processes,contract['limits']['cleanup_seconds'])
        except BaseException as error:
            cleanup=contract['limits']['cleanup_seconds'];failure={'complete':False,'validation_loaded':False,
                'phase':'cleanup','exception':type(error).__name__,'contract_sha256':c.sha(c.HERE/'contract.json'),
                'seconds':time.monotonic()-started,'partial_certificates_promoted':False}
        for log in logs:log.close()
        c.write(output/'supervisor.json',{'complete':failure is None,'phase':phase,'contract_sha256':c.sha(c.HERE/'contract.json'),
                'elapsed':time.monotonic()-started,'cleanup_seconds':cleanup,'returncodes':[p.returncode for p in processes]})
        if failure is not None:
            c.write(output/'failure.json',failure)
            if phase=='report':report.publish({'complete':False,'population':'fixed300_fit_only','validation_loaded':False,
                'contract_sha256':c.sha(c.HERE/'contract.json'),'failure_sha256':c.sha(output/'failure.json'),
                'predictions':{'P1':False,'P2':None,'P3':None}},output)
    if failure is not None:raise RuntimeError('phase incomplete; retained failure receipt')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('production','report'),required=True)
    ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--run',type=Path);a=ap.parse_args();main(a.phase,a.work,a.output,a.run)
