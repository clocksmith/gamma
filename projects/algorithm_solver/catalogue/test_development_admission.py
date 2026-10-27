import copy
import unittest
from unittest.mock import Mock

from .catalogue import BINDINGS, digest
from .development_admission import admit, sha, repository_license, review_sources


class DevelopmentAdmission(unittest.TestCase):
    def fixture(self):
        self.text = 'def solve(x):\n    return x + 1\n'
        interface = {'entrypoint': 'solve', 'arguments': 'ordered-positional'}
        bindings = {k: 'a' * 64 for k in BINDINGS}
        bindings.update(source_sha256=sha(self.text.encode()), interface_sha256=digest(interface))
        self.impl = dict(bindings, receipt_sha256='b' * 64, status='qualified')
        self.queue = {'summary': {'development_corpus_admitted': 0}, 'problems': [{
            'problem_id': 'leetcode:1', 'permission': 'source_access_authorized', 'split': None,
            'implementations': {'python': {'bindings': bindings, 'interface': interface,
                'qualification': {'receipt_binding_checked': True, 'receipt_sha256': 'b' * 64},
                'authoring_variants': {'records': [{'qualification_join': 'exact_existing_canonical_receipt'}]},
                'blockers': ['browser_execution_unavailable'], 'browser_guide_admitted': False}}}]}
        self.evidence = [{'problem_id': 'leetcode:1', 'language': 'python', 'kind': 'license',
                          'bindings': bindings, 'evidence': {'passed': True}}]
        self.service = Mock()
        self.service.request.return_value = {'artifact': {'status': 'materialized', 'source_utf8': self.text},
                                            'consumer_selection': {'implementation': self.impl}}
        self.license = Mock(return_value=True)
        self.host = Mock(return_value={'leetcode:1/python': {'unsupported': []}})

    def run_admit(self):
        return admit(self.queue, self.service, self.evidence, check_license=self.license, check_hosts=self.host)

    def test_source_admission_preserves_browser_and_split_boundaries(self):
        self.fixture(); before = copy.deepcopy(self.queue); result = self.run_admit()
        slot = result['problems'][0]['implementations']['python']
        self.assertTrue(slot['development_corpus_admitted'])
        self.assertFalse(slot['browser_guide_admitted'])
        self.assertEqual(slot['blockers'], ['browser_execution_unavailable'])
        self.assertIsNone(result['problems'][0]['split'])
        self.assertFalse(result['development_admission']['qualification_created'])
        self.assertEqual(before, self.queue)
        self.license.assert_called_once()
        self.host.assert_called_once_with({'leetcode:1/python': ('python', self.text)})

    def test_unknown_source_contract_or_permission_prevents_payload_reads(self):
        for mutate in [lambda row: row.update(permission='protected'),
                       lambda row: row['implementations']['python']['authoring_variants'].update(records=[]),
                       lambda row: row['implementations']['python']['qualification'].update(receipt_binding_checked=False)]:
            self.fixture(); mutate(self.queue['problems'][0]); self.host.return_value = {}
            self.assertEqual(self.run_admit()['summary']['development_corpus_admitted'], 0)
            self.service.request.assert_not_called()

    def test_flags_do_not_replace_license_or_host_verification(self):
        self.fixture(); self.license.return_value = False; self.host.return_value = {}
        self.assertEqual(self.run_admit()['summary']['development_corpus_admitted'], 0)
        self.fixture(); self.host.return_value['leetcode:1/python']['unsupported'] = ['external_io']
        self.assertEqual(self.run_admit()['summary']['development_corpus_admitted'], 0)
        self.assertFalse(repository_license('.', {'passed': True}, 'leetcode:1', 'python', self.text))

    def test_live_contract_or_source_drift_is_an_error(self):
        for key in ['source_sha256', 'problem_contract_sha256', 'tests_sha256', 'effects_sha256']:
            self.fixture(); self.impl[key] = 'c' * 64
            with self.assertRaisesRegex(ValueError, 'binding drift'): self.run_admit()

    def test_real_host_preflight_never_executes_source(self):
        result = review_sources({'one': ('python', 'raise RuntimeError("never execute")\ndef solve(x):\n    return x\n'),
                                 'two': ('javascript', 'function solve(){return Math.random()}')})
        self.assertEqual(result['one']['unsupported'], [])
        self.assertIn('reflection_or_nondeterministic_property:random', result['two']['unsupported'])


if __name__ == '__main__':
    unittest.main()
