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

class KnownSpecServiceV2Tests(KnownSpecServiceTests):
    """V2 controls use the real synthetic boundary validator, never a fake allow."""
    def setUp(self):
        super().setUp()
        from .test_boundary_policy import BoundaryPolicyTests
        raw, pins = BoundaryPolicyTests().fixture()
        paths = {}
        for name, data in raw.items():
            path = self.root / ('boundary-' + name + '.json'); path.write_bytes(data); paths[name] = str(path)
        self.gate = {'schema':'gamma.boundary-gate-config.v1','artifact_paths':paths,'trusted_hashes':pins}
        u = json.loads(raw['universe']); c = json.loads(Path(self.config['catalogue']['path']).read_text())
        c['universe_sha256'] = digest(u)
        for i in range(3,6):
            c['problems'].append({'problem_id':'leetcode:'+str(i),'implementations':{
                lang:{'status':'protected' if i<5 else 'blocked','reason':'synthetic boundary'} for lang in ('javascript','python')}})
        self.v2 = dict(self.config, schema='gamma.known-spec-service.v2',
            universe={'path':paths['universe'],'sha256':pins['universe']}, catalogue=self.write('v2-catalogue',c))
        self.s2 = {'schema':'gamma.known-spec-source-access.v2','boundary_gate':self.write('gate',self.gate),
            'locators':self.write('global-locators',{'schema':'gamma.dual.source-locators.v1',
                'problems':{'leetcode:1':{'python':str(self.root/'1.py')}}}),
            'authorized_problem_ids':['leetcode:1'], 'source_roots':[str(self.root)]}
        self.v2['source_access'] = self.s2

    def test_v2_global_exact_read_gate_called_before_open(self):
        from . import boundary_policy
        service = KnownSpecService(self.v2); calls=[]
        original = boundary_policy.authorize_before_open
        def gate(*a,**k): calls.append('gate'); return original(*a,**k)
        from .materialize import read_source
        def opener(*a,**k): self.assertEqual(calls,['gate']); calls.append('source'); return read_source(*a,**k)
        with patch('projects.algorithm_solver.catalogue.known_spec_service.boundary_policy.authorize_before_open',side_effect=gate), patch('projects.algorithm_solver.catalogue.known_spec_service.read_source',side_effect=opener):
            value=service.request('leetcode:1',language='python',include_source=True)
        self.assertEqual(value['artifact']['source_utf8'],self.data.decode()); self.assertEqual(calls,['gate','source'])

    def test_v2_every_open_rechecks_policy_drift(self):
        service=KnownSpecService(self.v2)
        self.assertEqual(service.request('leetcode:1',language='python',include_source=True)['status'],'matched')
        Path(self.gate['artifact_paths']['classification']).write_text('{}')
        with patch('projects.algorithm_solver.catalogue.known_spec_service.read_source',side_effect=AssertionError):
            self.assertEqual(service.request('leetcode:1',language='python',include_source=True)['reason'],'source_materialization_failed')

    def test_v2_valid_receipt_cannot_override_boundary_denial(self):
        service=KnownSpecService(self.v2)
        with patch('projects.algorithm_solver.catalogue.known_spec_service.boundary_policy.authorize_before_open',side_effect=PermissionError('reserved')), patch('projects.algorithm_solver.catalogue.known_spec_service.read_source',side_effect=AssertionError):
            self.assertEqual(service.request('leetcode:1',language='python',include_source=True)['status'],'abstain')

    def test_v2_reserved_unknown_cannot_be_located_or_authorized(self):
        for pid in ('leetcode:3','leetcode:4','leetcode:5'):
            source=dict(self.s2,authorized_problem_ids=[pid])
            with self.assertRaises(ValueError):KnownSpecService(dict(self.v2,source_access=source))
        service=KnownSpecService(self.v2)
        with patch('projects.algorithm_solver.catalogue.known_spec_service.read_source',side_effect=AssertionError):
            for pid in ('leetcode:3','leetcode:4','leetcode:5'):self.assertEqual(service.request(pid,language='python',include_source=True)['status'],'abstain')

    def test_v2_legacy_explicit_locator_alias_and_no_inference(self):
        alias={'schema':'gamma.numeric-id-alias-map.v1','from_universe_sha256':'a'*64,
            'to_universe_sha256':self.gate['trusted_hashes']['universe'],'access_policy_sha256':self.gate['trusted_hashes']['policy'],
            'aliases':{'development400:1':'leetcode:1'}}
        self.s2.update(aliases=self.write('v2-aliases',alias),development_universe_sha256='a'*64,
            locators=self.write('v2-legacy-locators',{'schema':'gamma.dual.source-locators.v1','problems':{'development400:1':{'python':str(self.root/'1.py')}}}))
        self.assertEqual(KnownSpecService(self.v2).request('leetcode:1',language='python',include_source=True)['status'],'matched')
        del self.s2['aliases'];del self.s2['development_universe_sha256']
        with self.assertRaises(ValueError):KnownSpecService(self.v2)

    def test_v2_duplicate_identity_locators_rejected(self):
        self.test_v2_legacy_explicit_locator_alias_and_no_inference()
        # Restore explicit alias then duplicate same canonical identity in global spelling.
        self.s2['aliases']={'path':str(self.root/'v2-aliases.json'),'sha256':hashlib.sha256((self.root/'v2-aliases.json').read_bytes()).hexdigest()}
        self.s2['development_universe_sha256']='a'*64
        self.s2['locators']=self.write('duplicate',{'schema':'gamma.dual.source-locators.v1','problems':{
            'leetcode:1':{'python':str(self.root/'1.py')},'development400:1':{'python':str(self.root/'1.py')}}})
        with self.assertRaises(ValueError):KnownSpecService(self.v2)

    def test_v2_locator_and_gate_file_drift(self):
        for key in ('locators','boundary_gate'):
            service=KnownSpecService(self.v2);path=Path(self.s2[key]['path']);old=path.read_bytes();path.write_text('{}')
            with patch('projects.algorithm_solver.catalogue.known_spec_service.read_source',side_effect=AssertionError):
                self.assertEqual(service.request('leetcode:1',language='python',include_source=True)['status'],'abstain')
            path.write_bytes(old)

    def test_v2_strict_unknown_config_fields(self):
        for config in (dict(self.v2,magic_allow=True),dict(self.v2,source_access=dict(self.s2,ignore_boundary=True))):
            with self.assertRaises(ValueError):KnownSpecService(config)

    def test_v2_rebind_preserves_qualified_and_all_receipts(self):
        from .known_spec_service import rebind_boundary_universe
        old=json.loads(Path(self.config['universe']['path']).read_text());c=json.loads(Path(self.v2['catalogue']['path']).read_text());r=json.loads(Path(self.config['verified_receipts']['path']).read_text())
        new=json.loads(Path(self.v2['universe']['path']).read_text());old=dict(new,protected_problem_ids=[]);c['universe_sha256']=digest(old)
        result,receipts,audit=rebind_boundary_universe(old,c,r,new,self.gate,predecessor_catalogue_sha256=digest(c))
        self.assertEqual(receipts,r);self.assertEqual(result['problems'][:2],c['problems'][:2]);self.assertEqual(audit['protected_after'],2)
        with self.assertRaises(ValueError):rebind_boundary_universe(old,c,r,new,self.gate,predecessor_catalogue_sha256='0'*64)

class StrictServiceMetadataTests(unittest.TestCase):
    def test_duplicate_fields_rejected_even_with_matching_pin(self):
        from .known_spec_service import _strict_spec
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'metadata.json';raw=b'{"schema":"x","schema":"y"}';path.write_bytes(raw)
            with self.assertRaises(ValueError):_strict_spec({'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()})
    def test_nonfinite_fields_rejected(self):
        from .known_spec_service import _strict_spec
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'metadata.json';raw=b'{"x":NaN}';path.write_bytes(raw)
            with self.assertRaises(ValueError):_strict_spec({'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()})
