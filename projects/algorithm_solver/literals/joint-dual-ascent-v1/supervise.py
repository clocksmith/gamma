"""Fresh-output, whole-phase supervision with independent failure publication."""
import argparse
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
import common as c
import report


def cleanup(processes,limit):
    started=time.monotonic()
    for process in processes:
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
    for process in processes:process.wait(timeout=max(.001,limit-(time.monotonic()-started)))
    return c.number(time.monotonic()-started,limit)


def main(phase,work,output,run=None):
    started=time.monotonic();deadline=started+1200;processes=[];logs=[];failure=None;result=None;where='preflight'
    def expired(*_):raise c.HardDeadline('Whole phase includes preflight and publication')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,1200)
    contract=None;cleanup_seconds=0
    try:
        if output.exists():raise FileExistsError('Fresh output directory required')
        output.mkdir(parents=True,exist_ok=False)
        contract=c.read(c.HERE/'contract.json');assert contract['limits'][phase+'_seconds']==1200
        resource.setrlimit(resource.RLIMIT_AS,(contract['limits']['address_space_bytes'],)*2)
        os.sched_setaffinity(0,{core for cores in contract['limits']['arm_cores'].values() for core in cores})
        c.check(contract)
        if phase=='report':assert run is not None and not list(run.glob('*failure.json')) and not list(run.glob('*/*failure.json'))
        where='workers'
        for cohort in ('R','naming'):
            log=(output/f'{cohort}.log').open('x');logs.append(log)
            command=[sys.executable,'-B',str(c.HERE/('run.py' if phase=='production' else 'report.py')),
                     '--cohort',cohort,'--work',str(work.resolve()),'--output',str(output.resolve()),'--deadline',str(deadline)]
            if phase=='report':command+=['--run',str(run.resolve())]
            processes.append(subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True))
        while True:
            codes=[p.poll() for p in processes]
            if any(code is not None and code!=0 for code in codes):raise RuntimeError('Worker failed')
            if all(code==0 for code in codes):break
            if time.monotonic()>=deadline:raise c.HardDeadline('Whole phase deadline')
            time.sleep(.05)
        where='collect'
        arms=[c.read(output/(name+'/results.json' if phase=='production' else name+'.json')) for name in ('R','naming')]
        assert all(a['complete'] is True and a['validation_loaded'] is False for a in arms)
        elapsed=c.number(time.monotonic()-started,1200)
        if phase=='production':
            result={'complete':True,'validation_loaded':False,'contract_sha256':c.sha(c.HERE/'contract.json'),'seconds':elapsed,'arms':arms}
        else:
            raw=c.read(run/'results.json')
            assert raw['complete'] is True and raw['contract_sha256']==c.sha(c.HERE/'contract.json')
            result={'schema':'gamma.joint-dual-ascent.report.v1','complete':True,'validation_loaded':False,
                    'population':'fixed300_fit_only','contract_sha256':c.sha(c.HERE/'contract.json'),
                    'private_results_sha256':c.sha(run/'results.json'),'production_seconds':raw['seconds'],
                    'replay_seconds':elapsed,'arms':arms,'predictions':{
                      'P1':True,'P2':any(a['targets']['best']['numerator']>a['targets']['zero']['numerator'] for a in arms),
                      'P3':any(a['targets']['best']['excludes_fixed300_joint_target'] for a in arms)}}
    except BaseException as error:
        failure={'complete':False,'validation_loaded':False,'phase':where,'exception':type(error).__name__,'partial_best_accepted':False}
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        cleanup_started=time.monotonic();signal.setitimer(signal.ITIMER_REAL,10)
        try:
            cleanup(processes,10)
            for log in logs:log.close()
            cleanup_seconds=c.number(time.monotonic()-cleanup_started,10)
        except BaseException as error:
            cleanup_seconds=time.monotonic()-cleanup_started
            failure={'complete':False,'validation_loaded':False,'phase':'cleanup','exception':type(error).__name__,'partial_best_accepted':False}
        finally:signal.setitimer(signal.ITIMER_REAL,0)
    # The guard is restored for final receipts/publication; failure cleanup gets
    # a separate ten-second allowance, never an accepted partial certificate.
    try:
        if failure is None:
            if time.monotonic()>=deadline:raise c.HardDeadline('Deadline before publication')
            signal.setitimer(signal.ITIMER_REAL,deadline-time.monotonic())
            c.write(output/'supervisor.json',{'complete':True,'phase':phase,'contract_sha256':c.sha(c.HERE/'contract.json'),
                    'elapsed':time.monotonic()-started,'cleanup_seconds':cleanup_seconds,'returncodes':[p.returncode for p in processes]})
            if phase=='report':report.publish(result,output)
            else:c.write(output/'results.json',result)
            c.number(time.monotonic()-started,1200)
            signal.setitimer(signal.ITIMER_REAL,0)
        else:raise RuntimeError('Phase incomplete')
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL,0)
        failure=failure or {'complete':False,'validation_loaded':False,'phase':'publication','exception':type(error).__name__,'partial_best_accepted':False}
        # Never overwrite an old production run on a refused repeated invocation.
        try:
            if failure['exception']!='FileExistsError' or phase=='report':
                c.write(output/'failure.json',failure)
                c.write(output/'supervisor.json',{'complete':False,'phase':phase,'contract_sha256':c.sha(c.HERE/'contract.json') if contract else None,
                        'elapsed':time.monotonic()-started,'cleanup_seconds':cleanup_seconds,'returncodes':[p.returncode for p in processes]})
        finally:
            if phase=='report':report.withdraw(output,error)
            elif failure['exception']!='FileExistsError':(output/'results.json').unlink(missing_ok=True)
        raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('production','report'),required=True);ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--run',type=Path);args=ap.parse_args()
    main(args.phase,args.work,args.output,args.run)
