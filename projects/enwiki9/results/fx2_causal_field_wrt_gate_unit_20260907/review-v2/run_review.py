#!/usr/bin/env python3
"""Focused synthetic review of actual canonical diagnostic timer semantics."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest

ROOT = Path('/home/x/deco/gamma/projects/enwiki9')
OUT = Path(__file__).resolve().parent
NAMES = ['tools/fx2_causal_field_wrt_gate_v2.py', 'tests/test_fx2_causal_field_wrt_gate_v2.py',
         'tools/enwiki9_lab.py', 'tools/run_with_resource_guard_v3.py',
         'tools/fx2_causal_field_replay_v1.py', 'tools/causal_field_wrt_adapter_v1.py',
         'tools/causal_field_parent_coder_v1.py', 'tools/causal_field_dependency_v1.py',
         'tools/wrt_exact.py']

def sources():
    return [{'path': name, 'bytes': (ROOT/name).stat().st_size,
             'sha256': hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name in NAMES]

before = sources()
assert before == json.loads((OUT/'expected-sources.json').read_text())
assert os.sched_getaffinity(0) == {3}
assert resource.getrlimit(resource.RLIMIT_AS)[0] == 536870912
assert resource.getrlimit(resource.RLIMIT_CPU)[0] == 60
assert resource.getrlimit(resource.RLIMIT_FSIZE)[0] == 33554432
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('author_v2_tests', ROOT/NAMES[1])
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)
observed = {}

class CanonicalTimerTests(unittest.TestCase):
    def test_actual_diagnostic_guard_expression_yields_null_without_calibration(self):
        source = ROOT/'tools/run_with_resource_guard_v3.py'
        tree = ast.parse(source.read_bytes())
        expressions = [node.value for node in ast.walk(tree) if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == 'wall_time_limit_seconds'
                               for target in node.targets)]
        self.assertEqual(len(expressions), 1)
        expression = ast.Expression(expressions[0])
        namespace = {'args': SimpleNamespace(geekbench5_single_core_score=None),
                     'objective_contract': {'resources': {'wallTime': {'maximumSecondsNumerator': 1}}}}
        actual = eval(compile(expression, str(source), 'eval'), namespace)
        self.assertIsNone(actual)
        observed['actual_uncalibrated_guard_wall_limit'] = actual

    def test_actual_outer_waiter_expires_job_and_requests_owned_group_kill(self):
        source = ROOT/'tools/enwiki9_lab.py'
        tree = ast.parse(source.read_bytes())
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == 'wait_for_budgeted_worker']
        self.assertEqual(len(nodes), 1)
        module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0),
                                 nodes[0]], type_ignores=[])
        ast.fix_missing_locations(module)
        timestamps = iter((10.0, 910.0, 910.0))
        populated = iter((True, False, False))
        writes, closed = [], []
        namespace = {'time': SimpleNamespace(monotonic=lambda: next(timestamps)),
                     'subprocess': subprocess, 'pathlib': __import__('pathlib'),
                     'os': SimpleNamespace(close=lambda descriptor: closed.append(descriptor)),
                     '_group_read': lambda descriptor, name: '1024' if name == 'memory.max' else '0',
                     '_group_write': lambda *args: writes.append(args),
                     '_group_populated': lambda descriptor: next(populated)}
        exec(compile(module, str(source), 'exec'), namespace)
        with tempfile.TemporaryDirectory() as temporary:
            group = Path(temporary)/'synthetic-group'
            group.mkdir()
            handles = [{'descriptor': 7, 'memory_bytes': 1024,
                        'path': str(group), 'inode': group.stat().st_ino}]
            job = {'resource_budget': {'wall_seconds': 900}, 'execution_resources': {}}
            process = SimpleNamespace(poll=lambda: 0)
            code = namespace['wait_for_budgeted_worker'](process, job, handles)
            self.assertEqual(code, 124)
            self.assertTrue(job['wall_budget_exceeded'])
            self.assertTrue(job['execution_resources']['cleanup_complete'])
            self.assertEqual(writes, [(7, 'cgroup.kill', '1\n')])
            self.assertEqual(closed, [7])
            self.assertFalse(group.exists())
        observed['extracted_outer_waiter_simulation'] = {'wall_seconds': 900, 'returncode': code,
                    'wall_budget_exceeded': True, 'owned_group_kill_requested': True,
                    'real_process_or_cgroup_created': False}

started = time.monotonic()
suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(author),
                           unittest.defaultTestLoader.loadTestsFromTestCase(CanonicalTimerTests)])
result = unittest.TextTestRunner(verbosity=2).run(suite)
after = sources()
self_usage = resource.getrusage(resource.RUSAGE_SELF)
child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
receipt = {'schema': 'focused-canonical-timer-review.v2', 'passed': result.wasSuccessful() and before == after,
           'tests_run': result.testsRun, 'errors': len(result.errors), 'failures': len(result.failures),
           'source_before': before, 'source_after': after, 'sources_unchanged': before == after,
           'canonical_semantics': observed, 'elapsed_seconds': time.monotonic()-started,
           'self_cpu_seconds': self_usage.ru_utime+self_usage.ru_stime,
           'child_cpu_seconds': child_usage.ru_utime+child_usage.ru_stime,
           'maximum_self_or_child_rss_kib': max(self_usage.ru_maxrss,child_usage.ru_maxrss),
           'scope': 'Synthetic v2 tests plus extracted unchanged canonical guard expression and outer waiter with fake clock/process/group operations. No corpus payloads, real jobs, or cgroups launched. Prior v1 clearance is superseded by the canonical null-wall mismatch.',
           'limits': {'cpus':[3], 'address_space_bytes':536870912,'cpu_seconds':60,'wall_seconds':90,'scratch_bytes':33554432},
           'objective_credit_bytes':0,'canonical_launch_authorized':False}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert result.wasSuccessful()
assert before == after
