import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from algsolve.synth import typed_confirmation as protocol, typed_codec as codec
from algsolve.synth import typed_development, typed_support


class TypedConfirmationTests(unittest.TestCase):
    def entry(self, slug='unopened-task'):
        return SimpleNamespace(key='lc:'+slug, slug=slug, members=['lcd:100'],
                               judge_uid='lcd:100', params=[['nums','List[int]']])

    def build(self, entry=None, pairs=None, exposure=None):
        e = entry or self.entry()
        source = {'source_sha256':protocol.mine.digest([e.__dict__]), 'confirmation_keys':[e.key]}
        problems = {'lcd:100':SimpleNamespace(evidence_ceiling='independent_tests_passed')}
        return protocol.build([e],problems,source,pairs or [],exposure or {'overlap_families':[]},'fixture',{})

    def test_reservation_does_not_claim_target_support_or_learning(self):
        result = self.build()
        self.assertEqual(result['reservation']['entries'],1)
        self.assertTrue(result['reservation']['pool'][0]['numeric_interface_candidate'])
        self.assertEqual(result['target_qualification']['status'],'pending')
        self.assertFalse(result['state']['target_cohort_qualified'])
        self.assertFalse(result['state']['training_started'])
        self.assertFalse(result['state']['evaluation_ready'])
        for forbidden in ('statement','reference_solutions','public_tests','hidden_tests'):
            self.assertNotIn(forbidden,result['reservation']['pool'][0])

    def test_unsupported_interfaces_remain_in_fixed_pool(self):
        e = self.entry(); e.params=[['words','List[str]']]
        result=self.build(e)
        self.assertEqual(result['reservation']['entries'],1)
        self.assertFalse(result['reservation']['pool'][0]['numeric_interface_candidate'])

    def test_unknown_duplicate_or_changed_reservation_fails(self):
        e=self.entry()
        for source in ({'source_sha256':'wrong','confirmation_keys':[e.key]},
                       {'source_sha256':protocol.mine.digest([e.__dict__]),'confirmation_keys':[e.key,e.key]},
                       {'source_sha256':protocol.mine.digest([e.__dict__]),'confirmation_keys':['lc:missing']}):
            with self.assertRaises(ValueError):
                protocol.build([e],{},source,[],{'overlap_families':[]},'fixture',{})

    def test_sibling_alias_exposure_and_training_overlap_fail_closed(self):
        found=protocol.exposed_families({'attempts':[{'uid':'lcd:alias'}], 'text':'ignored'},
                                        {'lcd:alias':'unopened-task-ii'})
        self.assertEqual(found,{'unopened-task'})
        with self.assertRaisesRegex(ValueError,'exposure'):
            self.build(exposure={'overlap_families':sorted(found)})
        with self.assertRaisesRegex(ValueError,'Development family'):
            self.build(pairs=[{'problem_family':'unopened-task'}])
        with self.assertRaisesRegex(ValueError,'Unknown exposure'):
            protocol.exposed_families({'uid':'unknown'}, {})

    def test_exposure_files_are_required_and_new_matching_files_are_inventoried(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaisesRegex(ValueError,'Missing exposure'):
                protocol.exposure_audit(root,{},set())
            for name in protocol.REQUIRED_EXPOSURES:
                path=root/name; path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text('' if path.suffix=='.jsonl' else '[]')
            before=protocol.exposure_audit(root,{}, {'unopened-task'})
            path=root/'later/pairs.jsonl'; path.parent.mkdir()
            path.write_text(json.dumps({'key':'lc:unopened-task-ii'})+'\n')
            after=protocol.exposure_audit(root,{}, {'unopened-task'})
            self.assertEqual(after['overlap_families'],['unopened-task'])
            self.assertEqual(len(after['sources']),len(before['sources'])+1)

    def test_development_bytes_graph_identity_support_and_overlap_are_checked(self):
        pairs=[]
        for row in typed_development.proposed():
            target=codec.encode(row['program'],'fixture')
            pairs.append({'uid':row['uid'],'problem_family':row['uid'],
                          'pattern_sha256':typed_support.pattern(row['program']),
                          'graph_sha256':codec.digest(target),'target':target,
                          'learning_split':'development_audit' if row['uid']=='lcd:3005' else 'development_fit'})
        with tempfile.TemporaryDirectory() as tmp:
            data=Path(tmp)/'pairs.jsonl'; summary=Path(tmp)/'summary.json'
            def write(rows):
                data.write_text(''.join(json.dumps(p)+'\n' for p in rows))
                summary.write_text(json.dumps({'artifacts_sha256':{'pairs.jsonl':protocol.sha(data)},
                                              'codec_sha256':'fixture','qualified_pairs':len(rows)}))
            write(pairs)
            self.assertEqual(len(protocol.verify_development(data,summary,'fixture')),len(pairs))
            data.write_text(data.read_text()+'\n')
            with self.assertRaisesRegex(ValueError,'corpus or codec'):
                protocol.verify_development(data,summary,'fixture')
            broken=copy.deepcopy(pairs); broken[0]['graph_sha256']='wrong'; write(broken)
            with self.assertRaisesRegex(ValueError,'graph identity'):
                protocol.verify_development(data,summary,'fixture')
            broken=copy.deepcopy(pairs)
            audit=next(p for p in broken if p['learning_split']=='development_audit')
            duplicate=copy.deepcopy(audit); duplicate['learning_split']='development_fit'; broken.append(duplicate)
            write(broken)
            with self.assertRaisesRegex(ValueError,'support/overlap'):
                protocol.verify_development(data,summary,'fixture')


if __name__=='__main__': unittest.main()
