"""Independent synthetic runner review; actual canonical guard matching via AST."""
import ast
import hashlib
import json
import os
from pathlib import Path
import pathlib
import resource
import sys
import time
import unittest
from unittest.mock import patch

ROOT = Path('/home/x/deco/gamma/projects/enwiki9')
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tests')]
import test_causal_field_opportunity_gate_v2 as author

gate = author.gate
PINS = {
    'tools/causal_field_opportunity_gate_v2.py': '7c1d59db38db1fa55ae8078af14eb8f87e904f2d85cda74a987315c08efc8ffe',
    'tests/test_causal_field_opportunity_gate_v2.py': '53f81dbf62379b475ab2e3e4ccc0f78b2d4a5918e13347a12cb988fa9aa4f79f',
}
INDEPENDENT_EVIDENCE = []
lab_source = (ROOT / gate.LAB).read_bytes()
lab_tree = ast.parse(lab_source, filename=str(ROOT / gate.LAB))
match_node, = [node for node in lab_tree.body
               if isinstance(node, ast.FunctionDef) and node.name == 'worker_pid_matches_job']
namespace = {'pathlib': pathlib, 'hashlib': hashlib, 'Any': object}
exec(compile(ast.Module(body=[match_node], type_ignores=[]), str(ROOT / gate.LAB), 'exec'), namespace)
canonical_matches = namespace['worker_pid_matches_job']


def proc_stat(pid, state='S', tick=1234):
    fields = [state] + ['0'] * 18 + [str(tick)] + ['0'] * 10
    return str(pid) + ' (synthetic guard) ' + ' '.join(fields)


class CanonicalGuardTests(unittest.TestCase):
    def test_real_canonical_matcher_accepts_exact_guard_and_rejects_identity_changes(self):
        cases = ('exact', 'vanished', 'zombie', 'foreign_boot', 'start_changed', 'command_changed')
        for case in cases:
            with self.subTest(case=case), author.main_fixture() as f:
                pid = f.job['worker_pid']
                command = b'python\0bound-guard\0bound-runner'
                f.job['execution_resources']['boot_id'] = 'synthetic-boot'
                f.job['execution_resources']['guard_command_sha256'] = hashlib.sha256(command).hexdigest()
                f.lab.worker_pid_matches_job = canonical_matches
                f.refresh()
                read_text, read_bytes = Path.read_text, Path.read_bytes
                guard_stat = Path('/proc') / str(pid) / 'stat'
                guard_command = Path('/proc') / str(pid) / 'cmdline'
                boot = Path('/proc/sys/kernel/random/boot_id')
                def proc_text(path, *args, **kwargs):
                    if path == guard_stat:
                        if case == 'vanished':
                            raise FileNotFoundError('synthetic vanished guard')
                        return proc_stat(pid, 'Z' if case == 'zombie' else 'S',
                                         1235 if case == 'start_changed' else 1234)
                    if path == boot:
                        return 'foreign-boot' if case == 'foreign_boot' else 'synthetic-boot'
                    return read_text(path, *args, **kwargs)
                def proc_bytes(path, *args, **kwargs):
                    if path == guard_command:
                        return (command + b'changed' if case == 'command_changed' else command) + b'\0'
                    return read_bytes(path, *args, **kwargs)
                with patch.object(Path, 'read_text', proc_text), patch.object(Path, 'read_bytes', proc_bytes):
                    if case == 'exact':
                        result = gate.main()
                        self.assertTrue(result['every_byte_state_agreement'])
                        self.assertTrue(result['retained_terminal_state_agreement'])
                        self.assertEqual(result['diagnostics']['inherited_selected_starts'], 1)
                        self.assertTrue((f.result / 'report.json').is_file())
                    else:
                        with self.assertRaisesRegex(ValueError, 'canonical live guard identity differs'):
                            gate.main()
                        self.assertFalse((f.result / 'report.json').exists())
                        self.assertNotIn(f.pop['modeled_path'], f.reads)
                        self.assertNotIn(f.pop['dictionary_path'], f.reads)
                INDEPENDENT_EVIDENCE.append({'case': case, 'canonical_guard_function_source': gate.LAB,
                    'canonical_guard_function_sha256': hashlib.sha256(ast.dump(match_node).encode()).hexdigest(),
                    'population_read': case == 'exact', 'report_published': case == 'exact',
                    'mocked': ['proc guard identity files', 'PPID', 'affinity', 'cgroup files'],
                    'real': ['canonical worker matcher function', 'source closure', 'runtime hash', 'synthetic scan']})


def main():
    assert os.sched_getaffinity(0) == {3}
    assert Path(os.environ['TMPDIR']) == OUT / 'tmp'
    for name, digest in PINS.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    source_paths = {p.relative_to(ROOT).as_posix() for p in author.closure.local_source_closure(
        [ROOT / gate.SELF, ROOT / gate.LAB, ROOT / gate.GUARD])} | gate.MANDATORY_SOURCES | set(PINS)
    sources = []
    for name in sorted(source_paths):
        data = (ROOT / name).read_bytes()
        target = OUT / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        sources.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    def scan_ast(path):
        tree = ast.parse(path.read_bytes())
        return ast.dump(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'scan'))
    assert scan_ast(ROOT / gate.SELF) == scan_ast(ROOT / 'tools/causal_field_opportunity_gate_v1.py')
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(author),
                               unittest.defaultTestLoader.loadTestsFromTestCase(CanonicalGuardTests)])
    start, cpu_start = time.monotonic(), time.process_time()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    elapsed, cpu = time.monotonic() - start, time.process_time() - cpu_start
    for row in sources:
        assert hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'], row['path']
    (OUT / 'main-evidence.json').write_text(json.dumps(author.MAIN_EVIDENCE, indent=2) + '\n')
    (OUT / 'canonical-guard-evidence.json').write_text(json.dumps(INDEPENDENT_EVIDENCE, indent=2) + '\n')
    (OUT / 'source-inventory.json').write_text(json.dumps(sources, indent=2) + '\n')
    receipt = {'tests': result.testsRun, 'author_tests': 15, 'independent_tests': 1,
               'independent_guard_cases': len(INDEPENDENT_EVIDENCE), 'passed': result.wasSuccessful(),
               'errors': len(result.errors), 'failures': len(result.failures),
               'source_count': len(sources), 'source_bytes': sum(r['bytes'] for r in sources),
               'source_unchanged_after_tests': True, 'scan_ast_unchanged_from_v1': True,
               'reviewed_pins': PINS, 'wall_seconds': elapsed, 'cpu_seconds': cpu,
               'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'scope': 'Synthetic main integration and admission only; no corpus or codec launch.',
               'timing_authority': 'shared-host diagnostic', 'corpus_bytes': 0,
               'new_codec_or_model_runs': 0, 'objective_credit_bytes': 0,
               'authority_limitation': 'Proc identity, cgroup, PPID, and affinity remain synthetic; real canonical matcher, schemas, source/runtime hashes, and synthetic scan are exercised.'}
    (OUT / 'review-execution.json').write_text(json.dumps(receipt, indent=2) + '\n')
    assert sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()) < 33554432
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
