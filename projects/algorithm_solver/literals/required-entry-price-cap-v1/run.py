"""One activated cohort; fixed construction, no validation or source execution."""
import signal
import time

class HardDeadline(BaseException): pass

def expired(*_): raise HardDeadline('600-second cohort deadline')

# Bootstrap before local imports, argument parsing or contract reads.
BOOT = time.monotonic()
if __name__ == '__main__':
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 600)

import argparse
import json
import math
import os
from pathlib import Path
import resource
if __name__ == '__main__':
    resource.setrlimit(resource.RLIMIT_AS, (8*1024**3,)*2)
    os.sched_setaffinity(0, {6, 7})
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ[name] = '1'
import binding as b


def failure_guard(deadline):
    remaining = deadline-time.monotonic()
    if remaining <= 0: raise HardDeadline('cohort failure publication deadline')
    signal.setitimer(signal.ITIMER_REAL, remaining)


def withdraw_worker(folder, failure, deadline):
    failure_guard(deadline)
    try: (folder/'results.json').unlink(missing_ok=True)
    except Exception: pass
    failure_guard(deadline)
    b.write(folder/'failure.json', failure)
    failure_guard(deadline)


def arm(cohort, work, output, deadline):
    started = BOOT if __name__ == '__main__' else time.monotonic()
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 600-(time.monotonic()-started)))
    folder = output/cohort; writable = False; phase = 'preflight'
    try:
        b.require_checks()
        assert type(deadline) in (int, float) and math.isfinite(deadline) and deadline > time.monotonic()
        deadline = min(deadline, started+600)
        signal.setitimer(signal.ITIMER_REAL, max(.001, deadline-time.monotonic()))
        resource.setrlimit(resource.RLIMIT_AS, (8*1024**3,)*2)
        os.sched_setaffinity(0, {'R': {6}, 'naming': {7}}[cohort])
        folder.mkdir(); writable = True
        c = b.read(b.HERE/'contract.json'); b.check_contract(c)
        b.write(folder/'status.json', {'complete': False, 'phase': phase})
        phase = 'input_identity_and_bans'; clock = time.monotonic()
        b.write(folder/'status.json', {'complete': False, 'phase': phase})
        inputs = b.load_inputs(c, work, cohort, deadline)
        input_seconds = time.monotonic()-clock
        phase = 'fresh_priced_prefix_coverage_required_allocation'; clock = time.monotonic()
        b.write(folder/'status.json', {'complete': False, 'phase': phase})
        import production
        proof, shape = production.execute(inputs, c, cohort)
        proof_seconds = time.monotonic()-clock
        result = {'schema': 'gamma.required-entry-price-cap.arm.v1', 'cohort': cohort, 'complete': True,
                  'validation_loaded': False, 'contract_sha256': b.sha(b.HERE/'contract.json'),
                  'bindings': inputs['bindings'], 'full_shape': shape, 'proof': proof,
                  'phase_seconds': {'input': input_seconds, 'proof': proof_seconds},
                  'seconds': time.monotonic()-started,
                  'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        b.number(result['seconds'], 600)
        assert time.monotonic() < deadline
        phase = 'publication'
        b.write(folder/'results.json', result)
        b.write(folder/'status.json', {'complete': True, 'phase': 'complete'})
        assert time.monotonic() < deadline
    except BaseException as error:
        if writable:
            emergency_deadline = min(time.monotonic()+10, deadline+10)
            withdraw_worker(folder, {'complete': False, 'validation_loaded': False,
                'phase': phase, 'exception': type(error).__name__,
                'seconds': time.monotonic()-started, 'partial_certificates_promoted': False},
                emergency_deadline)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--cohort', choices=('R', 'naming'), required=True)
    ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--deadline', type=float, required=True)
    a = ap.parse_args(); arm(a.cohort, a.work, a.output, a.deadline)
