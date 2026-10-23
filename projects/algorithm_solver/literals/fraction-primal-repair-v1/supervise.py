"""Whole-job wall guard and fail-closed immutable input/runtime checks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check_contract(c, work):
    if not __debug__ or sys.flags.optimize or 'PYTHONOPTIMIZE' in os.environ:
        raise RuntimeError('Normal assertion checks required')
    assert c['ready_to_freeze'] is True
    assert str(Path(sys.executable).absolute()) == c['python_bin']
    import numpy
    import scipy
    assert c['versions'] == {'python': platform.python_version(), 'numpy': numpy.__version__, 'scipy': scipy.__version__}
    assert os.environ.get('OMP_NUM_THREADS') == os.environ.get('OPENBLAS_NUM_THREADS') == os.environ.get('MKL_NUM_THREADS') == '1'
    for rel, digest in c['code_hashes'].items():
        assert sha(LIT / rel) == digest, rel
    for path, digest in c['runtime_files'].items():
        assert sha(path) == digest, path
    for rel, digest in c['private_files'].items():
        assert sha(work / rel) == digest, rel


def stop(processes):
    for p in processes:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    for p in processes:
        p.wait()


def main(work, output):
    started = time.monotonic(); c = json.loads((HERE / 'contract.json').read_text())
    deadline = started + c['limits']['overall_seconds']; processes = []; worker_deadlines = []; logs = []; phase = 'preflight'
    def expired(*_):
        raise TimeoutError('whole-job deadline reached')
    signal.signal(signal.SIGALRM, expired); signal.setitimer(signal.ITIMER_REAL, c['limits']['overall_seconds'])
    output.mkdir(parents=True, exist_ok=False)
    def write(path, value):
        path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    try:
        check_contract(c, work)
        os.sched_setaffinity(0, {i for cores in c['limits']['arm_cores'].values() for i in cores})
        phase = 'workers'
        for cohort in ('R', 'naming'):
            log = (output / f'{cohort}.log').open('w'); logs.append(log)
            worker_deadlines.append(min(deadline, time.monotonic() + c['limits']['cohort_seconds']))
            processes.append(subprocess.Popen([sys.executable, str(HERE / 'run.py'), '--cohort', cohort,
                '--work', str(work.resolve()), '--output', str(output.resolve()), '--deadline', str(worker_deadlines[-1])],
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True))
        while True:
            codes = [p.poll() for p in processes]
            if any(code is not None and code != 0 for code in codes):
                raise RuntimeError('worker failed; whole-job result rejected')
            if all(code == 0 for code in codes):
                break
            # Python SIGALRM may be deferred while a native solver is running.
            # The parent enforces each cohort's hard cap independently.
            if any(code is None and time.monotonic() >= limit for code, limit in zip(codes, worker_deadlines)):
                raise TimeoutError('cohort hard deadline reached')
            if time.monotonic() >= deadline:
                raise TimeoutError('whole-job deadline reached')
            time.sleep(.1)
        arms = [json.loads((output / cohort / 'results.json').read_text()) for cohort in ('R', 'naming')]
        assert all(a['complete'] is True and a['validation_loaded'] is False for a in arms)
        elapsed = time.monotonic() - started; assert elapsed <= c['limits']['overall_seconds']
        write(output / 'results.json', {'complete': True, 'validation_loaded': False, 'arms': arms,
              'seconds': elapsed, 'contract_sha256': sha(HERE / 'contract.json')})
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL, 0); stop(processes)
        write(output / 'failure.json', {'complete': False, 'validation_loaded': False, 'phase': phase,
              'exception': type(error).__name__, 'partial_witnesses_promoted': False,
              'seconds': time.monotonic() - started, 'contract_sha256': sha(HERE / 'contract.json')})
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0); stop(processes)
        for log in logs:
            log.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--work', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); a = p.parse_args(); main(a.work, a.output)
