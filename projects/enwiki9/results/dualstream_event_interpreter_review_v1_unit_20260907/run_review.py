"""Retain one independently bounded synthetic event-interpreter review attempt."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
ATTEMPT = BASE / 'attempt_01'
SOURCES = ('tools/dualstream_event_codec_v1.py', 'tools/dualstream_event_coder_v1.py',
           'tests/test_dualstream_event_interpreter_review_v1.py',
           'tools/dualstream_grammar_v1.py', 'tools/dualstream_grammar_reserialize_v1.py',
           'operations/provenance/dualstream_event_v1_plan.json')


def identity(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data if isinstance(data, bytes) else
                     (json.dumps(data, sort_keys=True, indent=2) + '\n').encode())


def limits():
    os.sched_setaffinity(0, {3})
    resource.setrlimit(resource.RLIMIT_AS, (512 << 20, 512 << 20))
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 << 20, 32 << 20))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.alarm(180)


def main():
    ATTEMPT.mkdir()
    (ATTEMPT / 'tmp').mkdir()
    refs = {name: identity(ROOT / name) for name in SOURCES}
    assert refs['tools/dualstream_event_coder_v1.py']['sha256'] == 'e6ea00ec70f2991a956d78a0e06f9f87d821051b9268ab89656cbd25deed1166'
    for name in SOURCES[:3]:
        write(ATTEMPT / 'source' / name, (ROOT / name).read_bytes())
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONHASHSEED='0',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               TMPDIR=str(ATTEMPT / 'tmp'),
               GAMMA_EVENT_REVIEW_RETAIN=str(ATTEMPT / 'fixtures'))
    command = [sys.executable, '-B', '-m', 'unittest', '-v',
               'tests.test_dualstream_event_interpreter_review_v1']
    start = time.monotonic()
    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    timeout = False
    with (ATTEMPT / 'regression.log').open('xb') as log:
        child = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log,
                                 stderr=subprocess.STDOUT, preexec_fn=limits,
                                 start_new_session=True)
        try:
            code = child.wait(timeout=180)
        except subprocess.TimeoutExpired:
            timeout = True
            os.killpg(child.pid, signal.SIGKILL)
            code = child.wait()
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    after = {name: identity(ROOT / name) for name in SOURCES}
    sizes = [p.stat().st_size for p in ATTEMPT.rglob('*') if p.is_file()]
    result = {'command': command, 'cwd': str(ROOT), 'cpu_affinity': [3],
              'thread_environment': {k: env[k] for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')},
              'limits': {'address_space_bytes': 512 << 20, 'cpu_seconds': 120,
                         'wall_seconds': 180, 'file_bytes': 32 << 20,
                         'scratch_bytes': 32 << 20, 'synthetic_raw_bytes_per_fixture': 8192},
              'exit_code': code, 'wall_timeout': timeout,
              'elapsed_seconds': time.monotonic() - start,
              'child_cpu_seconds': usage.ru_utime + usage.ru_stime - usage_before.ru_utime - usage_before.ru_stime,
              'child_peak_rss_kib': usage.ru_maxrss,
              'inputs_before': refs, 'inputs_after': after, 'source_unchanged': refs == after,
              'artifact_bytes_before_execution_receipt': sum(sizes),
              'scope': 'Four synthetic independent fixtures only; no corpus, gate, training or package qualification.'}
    write(ATTEMPT / 'execution.json', result)
    inventory = {str(p.relative_to(ATTEMPT)): identity(p) for p in sorted(ATTEMPT.rglob('*')) if p.is_file()}
    write(ATTEMPT / 'inventory.json', inventory)
    print(json.dumps(result, sort_keys=True))
    if code or timeout or refs != after or sum(sizes) > (32 << 20):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
