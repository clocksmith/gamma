"""Reviewed native launch supervisor; writes terminal failure even after child death.

Invocation is a launch action. Preparing/freezing this file is not authorization.
"""
import argparse,json,os,signal,subprocess,time
from pathlib import Path
from artifacts import pinned,sha
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]

def cleanup_group(child):
    """Only the session/group we created; always includes surviving descendants.

    A successful leader exit does not imply its process group is empty. TERM
    first, bounded direct-child reap, then KILL the owned group unconditionally.
    Orphan zombies may await system reaping; they cannot continue computation.
    """
    evidence={'process_group_id':child.pid,'term_sent':False,'kill_sent':False}
    try:
        os.killpg(child.pid,signal.SIGTERM);evidence['term_sent']=True
    except ProcessLookupError:pass
    try:child.wait(timeout=4)
    except subprocess.TimeoutExpired:pass
    try:
        os.killpg(child.pid,signal.SIGKILL);evidence['kill_sent']=True
    except ProcessLookupError:pass
    try:
        child.wait(timeout=1);evidence['leader_reaped']=True
    except subprocess.TimeoutExpired:evidence['leader_reaped']=False
    return evidence

def launch(args):
    f=pinned({'path':args.freeze,'sha256':args.freeze_sha256})
    for name,digest in f['code_sha256'].items():
        if sha(HERE/name)!=digest:raise ValueError('launcher/runner drift')
    if sha(Path(f['python']).resolve())!=f['encoder_cache_identity']['native_python_sha256']:raise ValueError('native interpreter pin')
    if f['resources']['wall_seconds']!=240:raise ValueError('wall scope')
    output=Path(args.output);output.mkdir(exist_ok=False)
    start=time.perf_counter();timed_out=False;code=None;error=None;child=None;cleanup=None
    env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',
             HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    try:
        with (output/'native.log').open('xb') as log:
            child=subprocess.Popen([f['python'],str(HERE/'run.py'),'--freeze',str(args.freeze),'--freeze-sha256',args.freeze_sha256,'--output',str(output/'results')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:code=child.wait(timeout=240)
            except subprocess.TimeoutExpired:
                timed_out=True
    except BaseException as exc:
        error=type(exc).__name__
    finally:
        if child is not None:
            cleanup=cleanup_group(child)
            code=child.returncode
    summary={'schema':'gamma.persistent-recognition-supervisor.v1','exit_code':code,'wall_timeout':timed_out,
             'error_type':error,'owned_group_cleanup':cleanup,'wall_seconds':time.perf_counter()-start,'freeze_sha256':args.freeze_sha256,
             'child_wall_budget_seconds':240,'termination_grace_seconds':5,'recognition_qualified':False}
    failed=code!=0 or timed_out or error is not None
    if not failed:
        try:
            report=json.loads((output/'results/report.json').read_text())
            if report['status']!='completed' or report['freeze_sha256']!=args.freeze_sha256 or len(report['requests'])!=14:
                raise ValueError('incomplete terminal report')
        except (OSError,ValueError,KeyError,TypeError):
            failed=True;summary['error_type']='MissingOrInvalidTerminalReport'
    summary['status']='failed' if failed else 'completed'
    (output/'supervisor.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    if failed and not (output/'results/failure.json').exists():
        (output/'failure.json').write_text(json.dumps(dict(summary,reason='child_failed_without_terminal_failure_manifest',
            incremental_results_path=str(output/'results/requests.jsonl')),sort_keys=True,indent=2)+'\n')
    return 1 if failed else 0

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('freeze','freeze-sha256','output'):p.add_argument('--'+name,required=True)
    raise SystemExit(launch(p.parse_args()))
