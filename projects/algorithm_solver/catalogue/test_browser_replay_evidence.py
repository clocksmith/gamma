import copy
import hashlib
import json
import unittest

from .browser_replay_evidence import verify
from .catalogue import BINDINGS


class BrowserEvidence(unittest.TestCase):
    def fixture(self):
        source = 'function solve(x) { return x + 1; }'
        bindings = {k: 'a' * 64 for k in BINDINGS}
        bindings['source_sha256'] = hashlib.sha256(source.encode()).hexdigest()
        self.queue = {'inputs': {'service_sha256': 'b' * 64}, 'problems': [{
            'problem_id': 'leetcode:1', 'permission': 'source_access_authorized',
            'implementations': {'javascript': {'bindings': bindings,
                'qualification': {'receipt_binding_checked': True, 'receipt_sha256': 'c' * 64}}}}]}
        row = {'problem_id': 'leetcode:1', 'source': source, **bindings,
               'receipt_sha256': 'c' * 64, 'entrypointAdapter': 'named-function-v1',
               'tests': [{'args': [1], 'expected': 2}]}
        self.bundle = {'service_sha256': 'b' * 64, 'rows': [row]}
        self.runner = {'runner.js': 'd' * 64, 'runner-frame.js': 'e' * 64}
        self.report = {'runner': self.runner, 'runtime_sha256': 'f' * 64,
            'externalRequests': [], 'browser_guides_admitted': 0, 'problems': 1,
            'rows': [{k: row[k] for k in ('problem_id', 'source_sha256', 'tests_sha256', 'receipt_sha256')} |
                     {'cases': 1, 'passed': True, 'batches': [{'start': 0, 'count': 1, 'passed': True, 'result': None}]}]}

    def run_verify(self):
        raw = json.dumps(self.bundle).encode(); bh = hashlib.sha256(raw).hexdigest()
        self.report['bundle_sha256'] = bh
        report = json.dumps(self.report).encode()
        return verify(raw, report, self.queue, bundle_sha256=bh,
                      report_sha256=hashlib.sha256(report).hexdigest(),
                      runner_hashes=self.runner, runtime_sha256='f' * 64)

    def test_exact_replay_is_evidence_without_admission(self):
        self.fixture(); original = copy.deepcopy(self.queue)
        result = self.run_verify()
        self.assertEqual(result['passed'], 1)
        evidence = result['records'][0]['evidence']
        self.assertTrue(evidence['return_mutation_batches_verified'])
        self.assertFalse(evidence['browser_guide_admission'])
        self.assertFalse(evidence['identity_alias_acceptance'])
        self.assertEqual(original, self.queue)

    def test_pass_flag_cannot_replace_complete_case_observations(self):
        for change in [lambda: self.report['rows'][0].update(batches=[]),
                       lambda: self.report['rows'][0]['batches'][0].update(start=1),
                       lambda: self.report['rows'][0]['batches'][0].update(passed=False, result='FAIL'),
                       lambda: self.report['rows'][0]['batches'][0].update(result='FAIL')]:
            self.fixture(); change()
            with self.assertRaises(ValueError): self.run_verify()

    def test_binding_permission_runtime_and_duplicate_drift_rejected(self):
        for change in [lambda: self.bundle['rows'][0].update(source='different'),
                       lambda: self.report['rows'][0].update(tests_sha256='0' * 64),
                       lambda: self.queue['problems'][0].update(permission='protected'),
                       lambda: self.report.update(runtime_sha256='0' * 64),
                       lambda: self.report.update(externalRequests=['https://example.com']),
                       lambda: self.report['rows'].append(self.report['rows'][0])]:
            self.fixture(); change()
            with self.assertRaises(ValueError): self.run_verify()

    def test_real_failure_is_retained_without_evidence_record(self):
        self.fixture(); self.report['rows'][0]['passed'] = False
        self.report['rows'][0]['batches'][0].update(passed=False, result='Sample failed')
        result = self.run_verify()
        self.assertEqual(result['failed_problem_ids'], ['leetcode:1'])
        self.assertEqual(result['records'], [])


if __name__ == '__main__':
    unittest.main()
