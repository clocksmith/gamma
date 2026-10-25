"""Reviewed native supervisor with owned-group cleanup and terminal evidence."""
import argparse,json,os,signal,subprocess,time
from pathlib import Path
from runtime import pinned,sha
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]

class TerminationSignal(BaseException):
    def __init__(self,signum):self.signum=signum

def _launch(args,state):
    f=pinned({'path':args.freeze,'sha256':args.freeze_sha256})
    for name,digest in f['code_sha256'].items():
        if sha(HERE/name)!=digest:raise ValueError('launcher/runner drift')
    if sha(Path(f['python']).resolve())!=f['native_python_sha256']:raise ValueError('native interpreter pin')
    if f['resources']['wall_seconds']!=240:raise ValueError('wall scope')
    output=Path(args.output);output.mkdir(exist_ok=False)
    start=time.perf_counter();start_monotonic=time.monotonic();timed_out=False;code=None;error=None;child=None;cleanup=None
    env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    from owned_supervisor import supervise
    argv=[f['python'],str(HERE/'run.py'),'--freeze',str(args.freeze),'--freeze-sha256',args.freeze_sha256,'--output',str(output/'results'),'--authorization',str(args.authorization),'--authorization-sha256',args.authorization_sha256,'--mode',args.mode]
    try:
        cleanup=supervise(argv,output/'native.log',start_monotonic+240,state,grace=0,rss_limit_bytes=f['resources']['owned_rss_limit_bytes'],env=env,cwd=ROOT)
        code=cleanup['exit_code'];timed_out=cleanup['wall_timeout'];error=cleanup['error_type']
        if cleanup['rss_limit_exceeded']:error='OwnedRSSLimitExceeded'
    except BaseException as exc:error=type(exc).__name__
    summary={'schema':'gamma.integrated-recognition-supervisor.v1','exit_code':code,'wall_timeout':timed_out,
             'error_type':error,'termination_signals':state['signals'],'owned_group_cleanup':cleanup,
             'wall_seconds':time.perf_counter()-start,'freeze_sha256':args.freeze_sha256,
             'child_wall_budget_seconds':240,'termination_grace_seconds':0,'cleanup_poll_budget_seconds':2,'recognition_qualified':False}
    failed=code!=0 or timed_out or error is not None or bool(state['signals'])
    if cleanup is not None and not cleanup.get('no_executing_owned_processes_observed',False):failed=True
    if not failed:
        try:
            report=json.loads((output/'results/report.json').read_text())
            if report['status']!='completed' or report['freeze_sha256']!=args.freeze_sha256 or len(report['requests'])!=f['runs'][args.mode]['queries']:raise ValueError('incomplete terminal report')
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
    for name in ('freeze','freeze-sha256','authorization','authorization-sha256','mode','output'):p.add_argument('--'+name,required=True)
    raise SystemExit(launch(p.parse_args()))
