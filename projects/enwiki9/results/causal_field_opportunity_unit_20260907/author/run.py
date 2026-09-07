"""Bounded synthetic test recorder; never open corpus or probability inputs."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time
import unittest

ROOT = Path('/home/x/deco/gamma/projects/enwiki9')
HERE = Path(__file__).resolve().parent
attempt = HERE / sys.argv[1]
attempt.mkdir()
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024**2, 32 * 1024**2))
signal.alarm(90)
assert os.sched_getaffinity(0) == {4}
os.chdir(ROOT)
sources = []
for name in ('tools/causal_field_opportunity_v1.py', 'tests/test_causal_field_opportunity_v1.py',
             'tools/causal_field_wrt_adapter_v1.py', 'tools/causal_field_dependency_v1.py', 'tools/wrt_exact.py'):
    raw = (ROOT / name).read_bytes()
    (attempt / Path(name).name).write_bytes(raw)
    sources.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
start = time.monotonic()
spec = importlib.util.spec_from_file_location('opportunity_tests', ROOT / 'tests/test_causal_field_opportunity_v1.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with (attempt / 'regression.log').open('w') as log:
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
elapsed = time.monotonic() - start
(attempt / 'synthetic-evidence.json').write_text(json.dumps(module.SYNTHETIC_EVIDENCE, sort_keys=True, indent=2) + '\n')
receipt = {'schema': 'gamma.enwiki9.field-opportunity-synthetic-unit.v1',
           'command': ['taskset', '--cpu-list', '4', 'timeout', '--signal=TERM', '--kill-after=2', '90',
                       sys.executable, '-B', str(Path(__file__).resolve()), sys.argv[1]],
           'cwd': str(ROOT), 'sources': sources,
           'run_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
           'passed': result.wasSuccessful(), 'elapsed_seconds': elapsed,
           'cpu_seconds': time.process_time(), 'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           'limits': {'cpus': [4], 'memory_bytes': 536870912, 'cpu_seconds': 60,
                      'wall_seconds': 90, 'scratch_bytes': 33554432},
           'corpus_reads': False, 'codec_runs': 0, 'source_mutations_during_tests': False,
           'synthetic_fixture_max_raw_bytes': max((row['raw_bytes'] for row in module.SYNTHETIC_EVIDENCE), default=0),
           'recorded_per_byte_parity_checks': sum(row['every_modeled_byte_parity_checks'] for row in module.SYNTHETIC_EVIDENCE),
           'objective_credit_bytes': 0, 'complete_package_bytes': None}
for row in sources:
    assert hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256']
receipt['artifacts'] = [{'path': str(path), 'bytes': path.stat().st_size,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                        for path in sorted(attempt.iterdir()) if path.is_file()]
assert sum(row['bytes'] for row in receipt['artifacts']) < 32 * 1024**2
(attempt / 'execution.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: receipt[key] for key in ('passed', 'tests', 'failures', 'errors', 'elapsed_seconds', 'cpu_seconds', 'peak_rss_kib', 'recorded_per_byte_parity_checks')}))
sys.exit(0 if result.wasSuccessful() else 1)
