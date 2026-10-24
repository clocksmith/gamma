"""Synthetic-only, fresh-output, single-deadline process-group supervisor."""
import time
STARTED=time.monotonic()
import argparse
import ctypes
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import fixtures
import pin_timing as pin

SECONDS=120
FAILURE_CLEANUP=10


class Deadline(BaseException): pass


def write(path,value):
    temporary=path.with_name(path.name+'.pending')
    temporary.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');temporary.replace(path)


def arm(deadline):
    remaining=deadline-time.monotonic()
    if remaining<=0:raise Deadline('Whole benchmark deadline')
    signal.setitimer(signal.ITIMER_REAL,remaining)


def subreaper():
    # Process-local adoption, not a host/system configuration change. It permits
    # bounded reaping of a killed coordinator's orphaned descendants.
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(36,1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'subreaper')


def stop(process,deadline):
    if process is None:return
    arm(deadline)
    try:os.killpg(process.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    process.wait(timeout=max(.001,deadline-time.monotonic()))
    while True:
        arm(deadline)
        try:pid,_=os.waitpid(-process.pid,os.WNOHANG)
        except ChildProcessError:return
        if not pid:time.sleep(min(.01,max(0,deadline-time.monotonic())))


def process_snapshot(root):
    """Only the owned worker and its descendants; no command/source reads."""
    todo=[root];seen=set();rows={}
    while todo:
        pid=todo.pop()
        if pid in seen:continue
        seen.add(pid)
        try:
            fields={line.split(':',1)[0]:line.split(':',1)[1].strip()
                    for line in Path(f'/proc/{pid}/status').read_text().splitlines() if ':' in line}
            rows[str(pid)]=int(fields.get('VmRSS','0 kB').split()[0])
            todo.extend(map(int,Path(f'/proc/{pid}/task/{pid}/children').read_text().split()))
        except (FileNotFoundError,ProcessLookupError):pass
    return rows


def coordinator(output,deadline):
    pin.require_checks();os.sched_setaffinity(0,{4});resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2)
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(Deadline()))
    arm(deadline);results=[]
    for block in fixtures.BLOCKS:
        arm(deadline);started=time.monotonic()
        command=[sys.executable,str(pin.HERE/'timing_worker.py'),'--block',block,
                 '--output',str(output),'--deadline',str(deadline)]
        process=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        peaks={};sampled_sum=0;samples=0
        while process.poll() is None:
            arm(deadline);sample=process_snapshot(process.pid);samples+=1
            sampled_sum=max(sampled_sum,sum(sample.values()))
            for pid,rss in sample.items():peaks[pid]=max(peaks.get(pid,0),rss)
            time.sleep(min(.02,max(0,deadline-time.monotonic())))
        if process.returncode!=0:raise RuntimeError('Synthetic worker failed')
        value=json.loads((output/(block+'.json')).read_text());assert value['complete'] is True and value['block']==block
        servicefile=output/(block+'-service.json')
        servicepid=str(json.loads(servicefile.read_text())['pid']) if servicefile.exists() else None
        value['end_to_end_seconds']=time.monotonic()-started
        value['memory_observation']={'sample_interval_seconds':.02,'samples':samples,
          'worker_sampled_peak_rss_kib':peaks.get(str(process.pid),0),
          'service_sampled_peak_rss_kib':None if servicepid is None else peaks.get(servicepid,0),
          'observed_per_pid_peak_rss_kib':peaks,'sampled_concurrent_sum_peak_kib':sampled_sum,
          'sum_of_observed_individual_peaks_kib':sum(peaks.values()),
          'scope':'Owned worker and descendants only; sampling can miss exited processes/peaks. Separate peaks are not simultaneous.'}
        results.append(value)
    assert len(results)==4 and all(x['semantics']==results[0]['semantics'] for x in results)
    value={'complete':True,'blocks':results,'fixture_sha256':fixtures.digest(fixtures.specification())}
    write(output/'coordinator.json',value);arm(deadline)


def command(output,deadline):
    return [sys.executable,str(pin.HERE/'timing.py'),'--coordinator','--output',str(output),'--deadline',str(deadline)]


def collect(output):
    value=json.loads((output/'coordinator.json').read_text())
    assert value['complete'] is True and value['fixture_sha256']==fixtures.digest(fixtures.specification())
    assert [b['block'] for b in value['blocks']]==list(fixtures.BLOCKS)
    assert all(b['complete'] is True and b['semantics']==value['blocks'][0]['semantics'] for b in value['blocks'])
    for b in value['blocks']:
        assert type(b['end_to_end_seconds']) in (int,float) and math.isfinite(b['end_to_end_seconds']) and b['end_to_end_seconds']>=0
    return value


def withdraw(output,failure,deadline):
    # Remove success markers before any fallible failure receipt write.
    for name in ('results.json','supervisor.json','REPORT.md'):
        arm(deadline)
        try:(output/name).unlink(missing_ok=True)
        except OSError:pass
    for name in ('failure.json','results.json','supervisor.json'):
        arm(deadline)
        try:write(output/name,failure)
        except Deadline:raise
        except BaseException:
            try:(output/name).unlink(missing_ok=True)
            except OSError:pass
    arm(deadline)
    try:(output/'REPORT.md').write_text('# Item52 incomplete\n\nNo accepted timing comparison.\n')
    except Deadline:raise
    except BaseException:
        try:(output/'REPORT.md').unlink(missing_ok=True)
        except OSError:pass


def main(output,expected_pin):
    pin.require_checks();started=STARTED;deadline=started+SECONDS
    process=None;writable=False;phase='preflight';result=None
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(Deadline()))
    arm(deadline)
    try:
        os.sched_setaffinity(0,{4});resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2)
        if output.exists():raise FileExistsError('Fresh output required')
        output.mkdir(parents=True);writable=True
        write(output/'supervisor.json',{'complete':False,'phase':'preflight','synthetic_only':True})
        config=pin.verify(expected_pin);assert config['synthetic_only'] is True
        subreaper();phase='workers'
        process=subprocess.Popen(command(output,deadline),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        process.wait(timeout=max(.001,deadline-time.monotonic()))
        if process.returncode!=0:raise RuntimeError('Coordinator failed')
        phase='collect';result=collect(output)
        phase='normal_cleanup';cleanup_started=time.monotonic();stop(process,deadline)
        cleanup=time.monotonic()-cleanup_started
        arm(deadline);phase='publication'
        result.update(schema='gamma.synthetic-parser-timing.v1',synthetic_only=True,
          private_inputs=False,pin_sha256=expected_pin,normal_cleanup_seconds=cleanup,
          seconds=time.monotonic()-started,aggregate_memory_cap_claim=False,
          scientific_followup_authorized=False)
        old=sum(b['end_to_end_seconds'] for b in result['blocks'] if b['block'].startswith('old'))
        new=sum(b['end_to_end_seconds'] for b in result['blocks'] if b['block'].startswith('persistent'))
        assert new>0
        result['old_to_persistent_sum_ratio']=old/new
        prose='# Item52 supplied-input timing\n\nAll four fixed blocks agree exactly on untimed semantic hashes/counts.\n'
        prose+=f'\nOld end-to-end sum: {old:.6f}s. Persistent sum: {new:.6f}s. Ratio: {old/new:.6f}.\n'
        prose+='\nStartup/cleanup are included. Two observations per path; no significance or corpus-runtime claim.\n'
        prose+='\nMemory is per-process accounting/sampled descendant RSS, not an aggregate cap or exact simultaneous peak.\n'
        temporary=output/'REPORT.md.pending';temporary.write_text(prose);temporary.replace(output/'REPORT.md')
        arm(deadline)
        write(output/'supervisor.json',{'complete':True,'synthetic_only':True,'pin_sha256':expected_pin,
          'seconds':time.monotonic()-started,'returncode':process.returncode,'normal_cleanup_seconds':cleanup})
        arm(deadline);write(output/'results.json',result);arm(deadline)
        signal.setitimer(signal.ITIMER_REAL,0)
        return result
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL,0)
        cleanup_deadline=time.monotonic()+FAILURE_CLEANUP
        failure={'complete':False,'synthetic_only':True,'phase':phase,'error_type':type(error).__name__,
                 'pin_sha256':expected_pin,'seconds':time.monotonic()-started,'comparison_accepted':False}
        try:
            arm(cleanup_deadline)
            # Kill first: failure-receipt I/O must never bypass descendant death.
            if process is not None:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
            # Withdrawal begins immediately, before potentially slow descendant cleanup.
            if writable:
                for name in ('results.json','supervisor.json','REPORT.md'):
                    arm(cleanup_deadline)
                    try:(output/name).unlink(missing_ok=True)
                    except OSError:failure['withdrawal_io_error']=True
            stop(process,cleanup_deadline)
        except BaseException as cleanup_error:failure['cleanup_error_type']=type(cleanup_error).__name__
        finally:
            try:
                arm(cleanup_deadline)
                if writable:withdraw(output,failure,cleanup_deadline)
            except BaseException:
                # Nonblocking best-effort final unlink after the cleanup alarm.
                if writable:
                    for name in ('results.json','supervisor.json','REPORT.md'):
                        try:(output/name).unlink(missing_ok=True)
                        except OSError:pass
            finally:signal.setitimer(signal.ITIMER_REAL,0)
        raise RuntimeError('Synthetic comparison incomplete; no accepted result') from error


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--pin-sha256');ap.add_argument('--coordinator',action='store_true');ap.add_argument('--deadline',type=float)
    args=ap.parse_args()
    if args.coordinator:
        assert args.deadline is not None and math.isfinite(args.deadline)
        coordinator(args.output.resolve(),args.deadline)
    else:
        if not args.pin_sha256:ap.error('--pin-sha256 required')
        main(args.output.resolve(),args.pin_sha256)
