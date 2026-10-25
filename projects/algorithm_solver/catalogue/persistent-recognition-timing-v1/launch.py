"""Reviewed native supervisor with owned-group cleanup and terminal evidence."""
import argparse,json,os,signal,subprocess,time
from pathlib import Path
from artifacts import pinned,sha
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]

class TerminationSignal(BaseException):
    def __init__(self,signum):self.signum=signum

def group_members(pgid):
    """Linux procfs observation: only non-zombie members can execute further."""
    live=[];unreadable=[]
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():continue
        try:
            text=(entry/'stat').read_text();fields=text[text.rfind(')')+2:].split()
            if int(fields[2])==pgid and fields[0] not in ('Z','X'):live.append(int(entry.name))
        except (FileNotFoundError,ProcessLookupError):pass
        except (PermissionError,ValueError,IndexError):unreadable.append(int(entry.name))
    return {'live_members':sorted(live),'inspection_unreadable_pids':sorted(unreadable)}

def cleanup_group(child):
    """TERM/KILL the complete new-session group even when its leader exited."""
    evidence={'process_group_id':child.pid,'term_sent':False,'kill_sent':False}
    try:os.killpg(child.pid,signal.SIGTERM);evidence['term_sent']=True
    except ProcessLookupError:pass
    try:child.wait(timeout=4)
    except subprocess.TimeoutExpired:pass
    try:os.killpg(child.pid,signal.SIGKILL);evidence['kill_sent']=True
    except ProcessLookupError:pass
    deadline=time.monotonic()+1
    while True:
        observed=group_members(child.pid)
        if not observed['live_members'] or time.monotonic()>=deadline:break
        time.sleep(.01)
    evidence.update(observed)
    try:child.wait(timeout=max(.01,deadline-time.monotonic()));evidence['leader_reaped']=True
    except subprocess.TimeoutExpired:evidence['leader_reaped']=False
    evidence['no_executing_group_members_observed']=not observed['live_members'] and not observed['inspection_unreadable_pids']
    return evidence

def _launch(args,state):
    f=pinned({'path':args.freeze,'sha256':args.freeze_sha256})
    for name,digest in f['code_sha256'].items():
        if sha(HERE/name)!=digest:raise ValueError('launcher/runner drift')
    if sha(Path(f['python']).resolve())!=f['encoder_cache_identity']['native_python_sha256']:raise ValueError('native interpreter pin')
    if f['resources']['wall_seconds']!=240:raise ValueError('wall scope')
    output=Path(args.output);output.mkdir(exist_ok=False)
    start=time.perf_counter();timed_out=False;code=None;error=None;child=None;cleanup=None
    env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    try:
        with (output/'native.log').open('xb') as log:
            if state['signals']:raise TerminationSignal(state['signals'][0])
            child=subprocess.Popen([f['python'],str(HERE/'run.py'),'--freeze',str(args.freeze),'--freeze-sha256',args.freeze_sha256,'--output',str(output/'results')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            deadline=time.monotonic()+240
            while True:
                if state['signals']:raise TerminationSignal(state['signals'][0])
                remaining=deadline-time.monotonic()
                if remaining<=0:timed_out=True;break
                try:code=child.wait(timeout=min(.1,remaining));break
                except subprocess.TimeoutExpired:pass
    except BaseException as exc:error=type(exc).__name__
    finally:
        # Handled termination arriving during cleanup/evidence writing is logged,
        # not allowed to interrupt cleanup and strand our detached group.
        state['finalizing']=True
        if child is not None:
            try:cleanup=cleanup_group(child);code=child.returncode
            except BaseException as exc:error='Cleanup'+type(exc).__name__
    summary={'schema':'gamma.persistent-recognition-supervisor.v1','exit_code':code,'wall_timeout':timed_out,
             'error_type':error,'termination_signals':state['signals'],'owned_group_cleanup':cleanup,
             'wall_seconds':time.perf_counter()-start,'freeze_sha256':args.freeze_sha256,
             'child_wall_budget_seconds':240,'termination_grace_seconds':5,'recognition_qualified':False}
    failed=code!=0 or timed_out or error is not None or bool(state['signals'])
    if cleanup is not None and not cleanup.get('no_executing_group_members_observed',False):failed=True
    if not failed:
        try:
            report=json.loads((output/'results/report.json').read_text())
            if report['status']!='completed' or report['freeze_sha256']!=args.freeze_sha256 or len(report['requests'])!=14:raise ValueError('incomplete terminal report')
        except (OSError,ValueError,KeyError,TypeError):failed=True;summary['error_type']='MissingOrInvalidTerminalReport'
    summary['status']='failed' if failed else 'completed'
    (output/'supervisor.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    if failed and not (output/'results/failure.json').exists():
        (output/'failure.json').write_text(json.dumps(dict(summary,reason='child_failed_without_terminal_failure_manifest',incremental_results_path=str(output/'results/requests.jsonl')),sort_keys=True,indent=2)+'\n')
    return 1 if failed else 0

def launch(args):
    state={'finalizing':False,'signals':[]};previous={}
    def handler(signum,frame):
        state['signals'].append(signum)
        # Flag-only handler closes the Popen-return/assignment signal race.
        # The active wait loop observes it within100ms; cleanup cannot be interrupted.
    try:
        for signum in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):
            previous[signum]=signal.signal(signum,handler)
        return _launch(args,state)
    finally:
        for signum,old in previous.items():signal.signal(signum,old)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('freeze','freeze-sha256','output'):p.add_argument('--'+name,required=True)
    raise SystemExit(launch(p.parse_args()))
