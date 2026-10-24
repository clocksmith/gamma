"""Absolute phase deadlines, worker/parser groups, cleanup before publication."""
import signal
import time

class HardDeadline(BaseException): pass

def expired(*_): raise HardDeadline('whole-phase deadline')

BOOT = time.monotonic()
if __name__ == '__main__':
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 1200)

import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

if __name__ == '__main__':
    resource.setrlimit(resource.RLIMIT_AS, (8*1024**3,)*2)
    os.sched_setaffinity(0, {6, 7})
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ[name] = '1'

import binding as b


def arm(deadline):
    """Never rearm an expired absolute budget after a one-shot signal fires."""
    remaining = deadline-time.monotonic()
    if remaining <= 0: raise HardDeadline('absolute cleanup/publication deadline')
    signal.setitimer(signal.ITIMER_REAL, remaining)
    return remaining


def stop(processes, seconds=10, *, deadline=None):
    started = time.monotonic(); first_error = None
    deadline = started+seconds if deadline is None else min(deadline, started+seconds)
    for proc in processes:
        arm(deadline)
        try: os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        except Exception as error:
            if first_error is None: first_error = error
    for proc in processes:
        remaining = arm(deadline)
        try: proc.wait(timeout=remaining)
        except Exception as error:
            if first_error is None: first_error = error
    arm(deadline)
    if first_error is not None: raise first_error
    return time.monotonic()-started


def withdraw(output, phase, error, module=None, *, deadline):
    """Remove success markers before failure I/O; deadlines always propagate."""
    for name in ('results.json', 'REPORT.md', 'supervisor.json'):
        arm(deadline)
        try: (output/name).unlink(missing_ok=True)
        except Exception: pass
    if phase == 'report' and module is not None:
        arm(deadline)
        try: module.withdraw(output, error, deadline=deadline)
        except Exception: pass
    arm(deadline)


def publish_failure(output, phase, failure, supervisor, module, deadline):
    # Independent withdrawal comes first, so ordinary failure-receipt I/O cannot
    # preserve successful artifacts. No subsequent operation follows a deadline.
    withdraw(output, phase, 'supervisor_failure', module, deadline=deadline)
    for name, value in [('failure.json', failure), ('supervisor.json', supervisor)]:
        arm(deadline)
        try: b.write(output/name, value)
        except Exception:
            arm(deadline)
            try: (output/name).unlink(missing_ok=True)
            except Exception: pass
    arm(deadline)


def main(phase, work, output, run=None):
    started = BOOT if __name__ == '__main__' else time.monotonic()
    deadline = started+1200
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, deadline-time.monotonic()))
    processes, logs = [], []; writable = False; failure = None; report = None
    contract_hash = None; where = 'preflight'; cleanup = 0; emergency_deadline = None
    try:
        b.require_checks()
        resource.setrlimit(resource.RLIMIT_AS, (8*1024**3,)*2)
        os.sched_setaffinity(0, {6, 7})
        for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ[name] = '1'
        assert phase in ('production', 'report')
        if output.exists():
            raise FileExistsError('fresh phase directory required')
        output.mkdir(parents=True); writable = True
        c = b.read(b.HERE/'contract.json')
        contract_hash = b.sha(b.HERE/'contract.json'); b.check_contract(c)
        if phase == 'report':
            import report as module
            report = module
            assert run is not None and not (run/'failure.json').exists()
        where = 'workers'
        for cohort in ('R', 'naming'):
            log = (output/f'{cohort}.log').open('w'); logs.append(log)
            command = [sys.executable, str(b.HERE/('run.py' if phase == 'production' else 'report.py')),
                       '--cohort', cohort, '--work', str(work.resolve()), '--output', str(output.resolve()),
                       '--deadline', str(deadline)]
            if phase == 'report': command += ['--run', str(run.resolve())]
            processes.append(subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True))
        while True:
            codes = [p.poll() for p in processes]
            if any(code is not None and (type(code) is not int or code != 0) for code in codes):
                raise RuntimeError('worker failed')
            if len(codes) == 2 and all(type(code) is int and code == 0 for code in codes): break
            if time.monotonic() >= deadline: raise HardDeadline('whole-phase deadline')
            time.sleep(.05)
    except BaseException as error:
        emergency_deadline = min(time.monotonic()+10, deadline+10)
        failure = {'complete': False, 'validation_loaded': False, 'phase': where,
                   'exception': type(error).__name__, 'contract_sha256': contract_hash,
                   'seconds': time.monotonic()-started, 'partial_certificates_promoted': False}
    finally:
        cleanup_started = time.monotonic(); cleanup_error = None
        cleanup_deadline = (emergency_deadline if emergency_deadline is not None
                            else min(cleanup_started+10, deadline))
        try:
            arm(cleanup_deadline)
            try: stop(processes, 10, deadline=cleanup_deadline)
            except Exception as error: cleanup_error = error
            for log in logs:
                arm(cleanup_deadline)
                try: log.close()
                except Exception as error:
                    if cleanup_error is None: cleanup_error = error
            arm(cleanup_deadline)
        except BaseException as error:
            if cleanup_error is None: cleanup_error = error
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
        cleanup = time.monotonic()-cleanup_started
        if cleanup_error is not None:
            if emergency_deadline is None:
                emergency_deadline = min(cleanup_started+10, deadline+10)
            failure = {'complete': False, 'validation_loaded': False, 'phase': 'cleanup',
                       'exception': type(cleanup_error).__name__, 'contract_sha256': contract_hash,
                       'seconds': time.monotonic()-started, 'partial_certificates_promoted': False}
    try:
        if failure is not None: raise RuntimeError('phase incomplete')
        remaining = deadline-time.monotonic()
        if remaining <= 0: raise HardDeadline('whole-phase deadline')
        signal.setitimer(signal.ITIMER_REAL, remaining)
        where = 'collect_after_cleanup'
        codes = [p.returncode for p in processes]
        assert len(codes) == 2 and all(type(code) is int and code == 0 for code in codes)
        elapsed = b.number(time.monotonic()-started, 1200)
        if phase == 'production':
            arms = []
            for cohort in ('R', 'naming'):
                folder = output/cohort
                assert not (folder/'failure.json').exists()
                receipt = b.read(folder/'results.json')
                assert receipt['cohort'] == cohort and receipt['complete'] is True and receipt['validation_loaded'] is False
                assert receipt['contract_sha256'] == contract_hash
                b.number(receipt['seconds'], min(600, elapsed))
                assert 0 < b.number(receipt['peak_rss_kib'], 8*1024**2)
                arms.append(receipt)
            result = {'complete': True, 'validation_loaded': False, 'contract_sha256': contract_hash,
                      'seconds': elapsed, 'arms': arms}
        else:
            result = report.combine(run, output, c, elapsed, codes)
        where = 'publication'
        arm(deadline)
        b.write(output/'supervisor.json', {'complete': True, 'phase': phase, 'contract_sha256': contract_hash,
                    'elapsed': time.monotonic()-started, 'cleanup_seconds': cleanup, 'returncodes': codes})
        arm(deadline)
        if phase == 'production': b.write(output/'results.json', result)
        else: report.publish(output, result)
        arm(deadline)
        b.number(time.monotonic()-started, 1200)
    except BaseException as error:
        if emergency_deadline is None:
            emergency_deadline = min(time.monotonic()+10, deadline+10)
        if failure is None:
            failure = {'complete': False, 'validation_loaded': False, 'phase': where,
                       'exception': type(error).__name__, 'contract_sha256': contract_hash,
                       'seconds': time.monotonic()-started, 'partial_certificates_promoted': False}
        if writable:
            publish_failure(output, phase, failure, {
                'complete': False, 'phase': phase, 'contract_sha256': contract_hash,
                'elapsed': time.monotonic()-started, 'cleanup_seconds': cleanup,
                'returncodes': [p.returncode for p in processes]}, report, emergency_deadline)
        raise RuntimeError('phase incomplete; no accepted certificate') from error
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--phase', choices=('production', 'report'), required=True)
    ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--run', type=Path)
    args = ap.parse_args(); main(args.phase, args.work, args.output, args.run)
