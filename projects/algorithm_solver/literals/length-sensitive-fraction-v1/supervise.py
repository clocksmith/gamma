"""Whole-job guard covering preflight, implicit construction, replay and output."""
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_contract(c, work):
    if not __debug__ or sys.flags.optimize or 'PYTHONOPTIMIZE' in os.environ:
        raise RuntimeError('assertions must be enabled')
    assert str(Path(sys.executable).absolute()) == c['python_bin']
    import numpy
    assert {'python': platform.python_version(), 'numpy': numpy.__version__} == c['versions']
    assert os.environ.get('OMP_NUM_THREADS') == os.environ.get('OPENBLAS_NUM_THREADS') == os.environ.get('MKL_NUM_THREADS') == '1'
    for rel, digest in c['code_hashes'].items():
        assert sha(LIT/rel) == digest, rel
    for path, digest in c['runtime_files'].items():
        assert sha(Path(path)) == digest, path
    for rel, digest in c['private_files'].items():
        assert sha(work/rel) == digest, rel


def stop_workers(processes):
    for process in processes:
        # The worker's process group also contains any ban-extraction children.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    for process in processes:
        process.wait()


def wait_workers(processes, deadline):
    while True:
        codes = [process.poll() for process in processes]
        if any(code is not None and code != 0 for code in codes):
            raise RuntimeError('worker failed; no whole-job certificate accepted')
        if all(code == 0 for code in codes):
            return
        if time.monotonic() >= deadline:
            raise TimeoutError('whole-job deadline reached')
        time.sleep(min(.1, max(0., deadline-time.monotonic())))


def main(work, output):
    started = time.monotonic()
    c = json.loads((HERE/'contract.json').read_text())
    deadline = started+c['limits']['overall_seconds']
    processes, logs = [], []
    phase='preflight'
    def expired(signum, frame):
        raise TimeoutError('whole-job deadline reached')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, c['limits']['overall_seconds'])
    output.mkdir(parents=True, exist_ok=False)
    try:
        check_contract(c, work)
        os.sched_setaffinity(0,{core for cores in c['limits']['arm_cores'].values() for core in cores})
        phase='workers'
        for cohort in ('R', 'naming'):
            log = (output/f'{cohort}.log').open('w')
            logs.append(log)
            processes.append(subprocess.Popen(
                [sys.executable, str(HERE/'run.py'), '--cohort', cohort,
                 '--work', str(work.resolve()), '--output', str(output.resolve()),
                 '--deadline', str(deadline)], stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True))
        wait_workers(processes, deadline)
        results = [json.loads((output/f'{cohort}-flex256/results.json').read_text()) for cohort in ('R', 'naming')]
        assert all(row['complete'] and not row['validation_loaded'] for row in results)
        (output/'results.json').write_text(json.dumps(
            {'arms': results, 'complete': True, 'validation_loaded': False,
             'contract_sha256': sha(HERE/'contract.json'), 'seconds': time.monotonic()-started},
            indent=2, sort_keys=True)+'\n')
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL, 0)
        stop_workers(processes)
        (output/'failure.json').write_text(json.dumps(
            {'complete': False, 'phase': phase, 'exception': type(error).__name__,
             'partial_certificates_promoted': False, 'validation_loaded': False,
             'contract_sha256': sha(HERE/'contract.json'), 'seconds': time.monotonic()-started},
            indent=2, sort_keys=True)+'\n')
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        stop_workers(processes)
        for log in logs:
            log.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main(args.work, args.output)
