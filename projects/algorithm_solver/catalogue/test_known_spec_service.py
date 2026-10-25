"""Synthetic file/metadata tests; candidate text is read but never executed."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from . import test_catalogue
from .catalogue import digest
from .known_spec_service import KnownSpecService, main


class KnownSpecServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        u, c, receipts = test_catalogue.Catalogue().fixture()
        u['eligible_problem_ids'] = ['leetcode:1', 'leetcode:2']
        c['universe_sha256'] = digest(u)
        self.data = b'def solve(x):\n    return x\n'
        (self.root / '1.py').write_bytes(self.data)
        new_receipts = {}
        for i, row in enumerate(c['problems'], 1):
            row['problem_id'] = 'leetcode:' + str(i)
            for impl in row['implementations'].values():
                receipt = receipts[impl['receipt_sha256']].copy()
                impl['source_sha256'] = hashlib.sha256(self.data).hexdigest()
                receipt.update(problem_id=row['problem_id'], source_sha256=impl['source_sha256'])
                rid = digest(receipt); impl['receipt_sha256'] = rid; new_receipts[rid] = receipt
        self.config = {'schema': 'gamma.known-spec-service.v1',
                       'universe': self.write('universe', u), 'catalogue': self.write('catalogue', c),
                       'verified_receipts': self.write('receipts', new_receipts)}
        self.source = {'access_policy':self.write('access_policy', {'schema':'gamma.all4081-source-access-policy.v1', 'new_source_access_authorized':False, 'source_publication_authorized':False, 'authorized_existing_source_problem_ids':['leetcode:1']}), 'aliases': self.write('aliases', {'schema':'gamma.numeric-id-alias-map.v1',
                          'from_universe_sha256':'a'*64, 'to_universe_sha256':self.config['universe']['sha256'],
                          'aliases':{'development400:1':'leetcode:1'}}),
                       'locators':self.write('locators', {'schema':'gamma.dual.source-locators.v1',
                          'problems':{'development400:1':{'python':str(self.root/'1.py')}}}),
                       'development_universe_sha256':'a'*64,
                       'authorized_problem_ids':['leetcode:1'], 'source_roots':[str(self.root)]}

    def write(self, name, obj):
        data=json.dumps(obj).encode(); path=self.root/(name+'.json'); path.write_bytes(data)
        return {'path':str(path),'sha256':hashlib.sha256(data).hexdigest()}

    def test_metadata_returns_both_languages_without_source_open(self):
        service=KnownSpecService(self.config)
        with patch('projects.algorithm_solver.catalogue.known_spec_service.read_source', side_effect=AssertionError):
            value=service.request('leetcode:1')
        self.assertEqual(set(value['implementations']), {'javascript','python'})
        self.assertNotIn('artifact',value)
        self.assertEqual(value['clarification_questions'],[])

    def test_unknown_and_invalid_identity_abstain(self):
        service=KnownSpecService(self.config)
        for pid in ('unknown', [], None): self.assertEqual(service.request(pid)['status'],'abstain')

    def test_source_requires_policy_and_consumer_language(self):
        service=KnownSpecService(self.config)
        self.assertEqual(service.request('leetcode:1',include_source=True)['reason'],'source_requires_consumer_language')
        self.assertEqual(service.request('leetcode:1',language='python',include_source=True)['reason'],'source_policy_required')

    def test_exact_synthetic_artifact_read_not_execution(self):
        service=KnownSpecService(dict(self.config,source_access=self.source))
        value=service.request('leetcode:1',language='python',include_source=True)
        self.assertEqual(value['artifact']['source_utf8'],self.data.decode())
        self.assertEqual(value['status'],'matched'); self.assertNotIn('example_passed',value)

    def test_outside_development_alias_abstains_before_open(self):
        service=KnownSpecService(dict(self.config,source_access=self.source))
        with patch('projects.algorithm_solver.catalogue.known_spec_service.read_source', side_effect=AssertionError):
            self.assertEqual(service.request('leetcode:2',language='python',include_source=True)['reason'],'source_not_authorized')
        self.source['authorized_problem_ids'].append('leetcode:2')
        with self.assertRaises(ValueError): KnownSpecService(dict(self.config,source_access=self.source))

    def test_source_hash_and_symlink_drift_abstain(self):
        service=KnownSpecService(dict(self.config,source_access=self.source))
        (self.root/'1.py').write_text('changed')
        self.assertEqual(service.request('leetcode:1',language='python',include_source=True)['reason'],'source_materialization_failed')
        (self.root/'1.py').unlink(); (self.root/'1.py').symlink_to(self.root/'catalogue.json')
        self.assertEqual(service.request('leetcode:1',language='python',include_source=True)['reason'],'source_materialization_failed')

    def test_roots_and_alias_universe_fail_closed(self):
        self.source['source_roots']=[str(self.root/'other')]
        service=KnownSpecService(dict(self.config,source_access=self.source))
        self.assertEqual(service.request('leetcode:1',language='python',include_source=True)['reason'],'source_outside_pinned_roots')
        self.source['development_universe_sha256']='c'*64
        with self.assertRaises(ValueError): KnownSpecService(dict(self.config,source_access=self.source))

    def test_protected_slots_abstain_and_cannot_be_authorized(self):
        u=json.loads(Path(self.config['universe']['path']).read_text())
        c=json.loads(Path(self.config['catalogue']['path']).read_text())
        u['protected_problem_ids']=['leetcode:1']; c['universe_sha256']=digest(u)
        for language in ('javascript','python'):
            c['problems'][0]['implementations'][language]={'status':'protected','reason':'closed'}
        self.config['universe']=self.write('universe',u); self.config['catalogue']=self.write('catalogue',c)
        service=KnownSpecService(self.config)
        with patch('projects.algorithm_solver.catalogue.known_spec_service.read_source', side_effect=AssertionError):
            self.assertEqual(service.request('leetcode:1',language='python',include_source=True)['status'],'abstain')
        aliases=json.loads(Path(self.source['aliases']['path']).read_text())
        aliases['to_universe_sha256']=self.config['universe']['sha256'];self.source['aliases']=self.write('aliases',aliases)
        with self.assertRaises(ValueError): KnownSpecService(dict(self.config,source_access=self.source))

    def test_mandatory_source_policy_cannot_be_omitted_or_expanded(self):
        source=dict(self.source);del source['access_policy']
        with self.assertRaises(KeyError): KnownSpecService(dict(self.config,source_access=source))
        policy=json.loads(Path(self.source['access_policy']['path']).read_text())
        policy['new_source_access_authorized']=True
        self.source['access_policy']=self.write('access_policy',policy)
        with self.assertRaises(ValueError): KnownSpecService(dict(self.config,source_access=self.source))

    def test_pinned_config_and_artifact_hashes(self):
        spec=self.write('config',self.config)
        self.assertEqual(KnownSpecService.from_config(spec['path'],spec['sha256']).request('leetcode:1')['status'],'matched')
        with self.assertRaises(ValueError): KnownSpecService.from_config(spec['path'],'0'*64)
        Path(self.config['catalogue']['path']).write_text('{}')
        with self.assertRaises(ValueError): KnownSpecService(self.config)

    def test_cli_is_runnable_and_invalid_config_abstains(self):
        spec=self.write('config',self.config)
        for sha,expected in ((spec['sha256'],0),('0'*64,2)):
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                status=main(['--config',spec['path'],'--config-sha256',sha,'--problem-id','leetcode:1'])
            self.assertEqual(status,expected)
            self.assertEqual(json.loads(output.getvalue())['status'],'matched' if expected==0 else 'abstain')


if __name__ == '__main__': unittest.main()
