"""Record bounded synthetic v2 admission tests; no corpus is opened."""
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
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
resource.setrlimit(resource.RLIMIT_FSIZE, (33554432, 33554432))
signal.alarm(90)
assert os.sched_getaffinity(0) == {4}
os.chdir(ROOT)
sources = []
for name in ('tools/causal_field_opportunity_gate_v2.py', 'tests/test_causal_field_opportunity_gate_v2.py',
             'tools/causal_field_opportunity_v1.py', 'tools/causal_field_wrt_adapter_v1.py',
             'tools/causal_field_dependency_v1.py', 'tools/wrt_exact.py',
             'tools/enwiki9_python_source_closure.py', 'tools/enwiki9_lab.py', 'tools/run_with_resource_guard_v3.py'):
    raw = (ROOT / name).read_bytes()
    (attempt / Path(name).name).write_bytes(raw)
    sources.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
start = time.monotonic()
spec = importlib.util.spec_from_file_location('opportunity_gate_v2_tests', ROOT / 'tests/test_causal_field_opportunity_gate_v2.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with (attempt / 'regression.log').open('w') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
elapsed = time.monotonic() - start
(attempt / 'main-evidence.json').write_text(json.dumps(module.MAIN_EVIDENCE, sort_keys=True, indent=2) + '\n')
receipt = {'schema': 'gamma.enwiki9.opportunity-gate-v2-unit.v1',
           'command': ['taskset', '--cpu-list', '4', 'timeout', '--signal=TERM', '--kill-after=2', '90',
                       sys.executable, '-B', str(Path(__file__).resolve()), sys.argv[1]],
           'cwd': str(ROOT), 'sources': sources,
           'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
           'passed': result.wasSuccessful(), 'elapsed_seconds': elapsed,
           'cpu_seconds': time.process_time(), 'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           'limits': {'cpus': [4], 'memory_bytes': 536870912, 'cpu_seconds': 60, 'wall_seconds': 90, 'scratch_bytes': 33554432},
           'mock_main_authority': 'External lab worker identity, PPID, affinity and cgroup files are mocked. Contract/job JSON schemas, local source bytes, interpreter hash and synthetic modeled scan are real.',
           'raw_fixture_bytes': len(module.fixture()[0]), 'corpus_bytes': 0, 'new_codec_or_model_runs': 0,
           'objective_credit_bytes': 0, 'complete_package_bytes': None}
for row in sources:
    assert hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256']
receipt['artifacts'] = [{'path': str(path), 'bytes': path.stat().st_size,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                        for path in sorted(attempt.iterdir()) if path.is_file()]
assert sum(row['bytes'] for row in receipt['artifacts']) < 33554432
(attempt / 'execution.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: receipt[key] for key in ('passed', 'tests', 'failures', 'errors', 'elapsed_seconds', 'cpu_seconds', 'peak_rss_kib')}))
sys.exit(0 if result.wasSuccessful() else 1)
