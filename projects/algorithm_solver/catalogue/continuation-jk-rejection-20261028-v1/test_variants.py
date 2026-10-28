"""Wrapper/host agreement and judge detection on toy programs; never loads J/K candidates."""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'continuation-jk-qualification-20261028-v1'))
sys.path.insert(0, str(HERE))
import protocol as jk  # noqa: E402
from variants import LARGE, OPERATORS, triggers, variant_source  # noqa: E402

TOYS = {
    ('python', 'list'): b'def solve(nums, k):\n    return [x + k for x in nums]\n',
    # Deep self-recursion: an extra wrapper frame per level would exceed the default limit.
    ('python', 'int'): b'import sys\nsys.setrecursionlimit(1100)\ndef solve(nums, k, i=0):\n    return 0 if i == len(nums) else nums[i] + (k if i == 0 else 0) + solve(nums, k, i + 1)\n',
    ('python', 'str'): b'def solve(nums, k):\n    return ",".join(str(x + k) for x in nums)\n',
    ('python', 'bool'): b'def solve(nums, k):\n    return sum(nums) > k\n',
    ('javascript', 'str'): b'"use strict";\nfunction solve(nums, k) { return nums.map(x => x + k).join(","); }\nmodule.exports=solve;\n',
    ('javascript', 'bool'): b'"use strict";\nfunction solve(nums, k) { return nums.reduce((a, b) => a + b, 0) > k; }\nmodule.exports=solve;\n',
    ('javascript', 'list'): b'"use strict";\nfunction solve(nums, k) { return nums.map(x => x + k); }\nmodule.exports=solve;\n',
    ('javascript', 'int'): b'"use strict";\nfunction solve(nums, k) { return nums.length ? nums[0] + k + solve(nums.slice(1), 0) : 0; }\nmodule.exports=solve;\n',
}
ARGS = [[[], 0], [[5], 2], [[1, 1, 2], 3], [[-1, 4, 7], 1], [[3, 4], 0], [list(range(LARGE)), 1]]
PID = jk.IDS['j'][0]  # exact-policy cohort id; owner predicates are not consulted for J


def expected(shape, nums, k):
    if shape == 'str':
        return ','.join(str(x + k) for x in nums)
    if shape == 'bool':
        return sum(nums) > k
    return [x + k for x in nums] if shape == 'list' else sum(nums) + (k if nums else 0)


def observe(language, program, calls):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp/'inputs.json').write_text(json.dumps({'entry': 'solve', 'calls': [{'args': a} for a in calls]}))
        if language == 'python':
            (tmp/'program.py').write_bytes(program)
            shutil.copy(jk.ROOT/jk.TRANSPORT/'harness.py', tmp/'harness.py')
            argv = [sys.executable, '-I', '-S', 'harness.py']
        else:
            (tmp/'program.js').write_bytes(program)
            shutil.copy(jk.ROOT/jk.FUNCTION_TRANSPORT, tmp/'harness.cjs')
            shutil.copy(jk.ROOT/jk.TRANSPORT/'harness.cjs', tmp/'observer.cjs')
            argv = ['node', 'harness.cjs']
        done = subprocess.run(argv, cwd=tmp, capture_output=True, timeout=60)
        return done.returncode, done.stdout


class VariantTests(unittest.TestCase):
    def check(self, language, shape, op):
        cases = [{'args': a, 'expected': expected(shape, *a)} for a in ARGS]
        code, stdout = observe(language, variant_source(TOYS[(language, shape)], language, op), [c['args'] for c in cases])
        self.assertEqual(code, 0)
        records = jk.parse(stdout, len(cases))
        for position, (case, record) in enumerate(zip(cases, records)):
            reason = jk.compare(PID, language, case, record, None)
            fired = triggers(op, language, case['args'], position, case['expected'])
            if fired:
                self.assertIn(reason, OPERATORS[op][1], (language, shape, op, position, record))
            else:
                self.assertIsNone(reason, (language, shape, op, position, record))
        return records

    def test_detectable_operators_fire_exactly_where_the_host_predicts(self):
        detectable = [op for op, (kind, _) in OPERATORS.items() if kind != 'resource']
        for language in ('python', 'javascript'):
            for shape in ('list', 'int', 'str', 'bool'):
                for op in detectable:
                    with self.subTest(language=language, shape=shape, op=op):
                        self.check(language, shape, op)

    def test_every_value_trigger_fires_on_the_toy_suite(self):
        for op in OPERATORS:
            if OPERATORS[op][0] in ('value', 'state', 'interface', 'effects'):
                self.assertTrue(any(triggers(op, 'python', a, i, expected('list', *a)) for i, a in enumerate(ARGS)), op)
        self.assertTrue(any(triggers('alias-equal-input', 'javascript', a, i, expected('list', *a)) for i, a in enumerate(ARGS)))

    def test_recursive_inner_calls_pass_through_unchanged(self):
        for language in ('python', 'javascript'):
            records = self.check(language, 'int', 'wrong-always')
            self.assertEqual(records[3]['result'], expected('int', [-1, 4, 7], 1)+1)

    def test_resource_triggers_only_large_inputs_and_bigints_stay_ignored(self):
        for op in ('slow-on-large', 'memory-on-large', 'wrong-on-large'):
            self.assertTrue(triggers(op, 'python', ARGS[-1], 0, None))
            self.assertFalse(triggers(op, 'javascript', [[1]*(LARGE-1), 'x'], 0, None))
        big = {'__gamma_bigint_v1__': str(2**60)}
        for language in ('python', 'javascript'):
            self.assertFalse(triggers('wrong-on-duplicates', language, [[big, big]], 0, None))
            self.assertFalse(triggers('wrong-on-negative', language, [[{'__gamma_bigint_v1__': str(-2**60)}]], 0, None))

    def test_javascript_lengths_count_utf16_units(self):
        self.assertTrue(triggers('wrong-on-degenerate', 'python', ['\U0001F600'], 0, None))
        self.assertFalse(triggers('wrong-on-degenerate', 'javascript', ['\U0001F600'], 0, None))

    def test_variant_preserves_original_bytes_and_rejects_unknown_operators(self):
        source = TOYS[('python', 'list')]
        self.assertTrue(variant_source(source, 'python', 'wrong-always').startswith(source))
        with self.assertRaises(ValueError):
            variant_source(source, 'python', 'nonexistent')


class RejectionPlanTests(unittest.TestCase):
    def test_plan_targets_triggering_batches_and_classifies_outcomes(self):
        import rejection
        pid = jk.IDS['j'][0]
        rows = [{'args': a, 'expected': expected('list', *a)} for a in ARGS]
        data = {p: rows for key in jk.IDS for p in jk.IDS[key]}
        contract = {'batch_plans': {str(p): {'batches': [{'indices': [0, 1, 0]}, {'indices': [5]}]} for p in data}}
        eligible = {(p, lang): {'admitted_cases_passed': p == pid} for p in data for lang in jk.LANGUAGES}
        entries = rejection.plan(data, contract, eligible)
        mine = {(e['language'], e['operator']): e for e in entries if e['problem_id'] == pid}
        self.assertEqual(mine[('python', 'wrong-on-large')]['batches'], [1])
        self.assertEqual(mine[('python', 'control-copy')]['batches'], [0, 1])
        self.assertEqual(mine[('javascript', 'wrong-on-repeat-call')]['batches'], [0])
        self.assertEqual(mine[('python', 'wrong-on-negative')]['status'], 'not_triggered')
        self.assertEqual(next(e for e in entries if e['problem_id'] != pid)['status'], 'original_not_passing')
        entry = mine[('python', 'input-mutation')]
        self.assertEqual(rejection.classify(entry, []), 'false_acceptance')
        self.assertEqual(rejection.classify(entry, [{'case': 0, 'reason': 'input_effects'}]), 'rejected_confirming')
        self.assertEqual(rejection.classify(entry, [{'case': 0, 'reason': 'result_value'}]), 'rejected_other')
        self.assertEqual(rejection.classify(mine[('python', 'wrong-on-large')], [{'case': 0, 'reason': 'result_value'}]), 'rejected_other')
        self.assertEqual(rejection.classify(mine[('python', 'control-copy')], [{'case': 5, 'reason': 'x'}]), 'control_rejected')


if __name__ == '__main__':
    unittest.main()
