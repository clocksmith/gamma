import copy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from algsolve.records import Problem
from algsolve.synth import typed_codec as codec, typed_development as dev, typed_support
from algsolve.synth import typed_target_qualification as qualification


class ProtectedQualificationTests(unittest.TestCase):
    def setUp(self):
        # Development fixtures only: these tests never read reserved problems.
        self.pairs = []
        for row in dev.proposed():
            target = codec.encode(row['program'], 'fixture')
            self.pairs.append({'uid': row['uid'], 'problem_family': row['uid'],
                              'target': target, 'pattern_sha256': typed_support.pattern(row['program']),
                              'learning_split': 'development_fit'})
        graph = copy.deepcopy(dev.proposed()[0]['program'])
        graph['return'] = {'op': 'add', 'args': [graph['return'], {'literal': 1}]}
        self.problem = Problem(uid='fixture:new', source='fixture', source_id='new', title='Fixture',
                               slug='fixture', statement='fixture statement', io_mode='functional',
                               entry={'class': 'Solution', 'method': 'solve'}, params=[['nums','List[int]']],
                               public_tests=[{'args': [[1]], 'expected': 1}], evidence_ceiling='independent_tests_passed')
        self.row = {'key': 'lc:fixture', 'disposition': 'candidate', 'program': graph,
                    'requirements': {'declared_input_bounds': 'fixture', 'complexity_review': 'fixture'},
                    'bound_probe': {'args': [[1]], 'expected': 1}, 'proposer': 'fixture',
                    'problem_sha256': qualification.problem_identity(self.problem)}
        self.entry = {'key': 'lc:fixture', 'judge_uid': self.problem.uid, 'family': 'fixture'}
        self.contract = {'reservation': {'pool': [self.entry]}}
        self.loader = Mock(return_value=[{'args': [[2]], 'expected': 7}])
        self.judge = Mock(return_value=SimpleNamespace(passed=True, to_dict=lambda: {'passed': True, 'tests_passed': 1}))

    def call(self):
        return qualification.qualify(self.row, self.entry, self.problem, self.pairs, 'fixture',
                                     judge=self.judge, independent_loader=self.loader)

    def test_fixed_denominator_and_explicit_exclusions(self):
        qualification.validate_proposals([self.row], self.contract)
        for rows in ([], [self.row,self.row], [{**self.row,'key':'lc:other'}]):
            with self.assertRaises(ValueError): qualification.validate_proposals(rows,self.contract)
        excluded={'key':'lc:fixture','disposition':'excluded','reason':'unsupported_interface','detail':'fixture'}
        qualification.validate_proposals([excluded], self.contract)
        self.row=excluded
        record,target=self.call()
        self.assertEqual(record['status'],'excluded'); self.assertIsNone(target)
        self.loader.assert_not_called(); self.judge.assert_not_called()

    def test_support_failure_never_loads_independent_tests(self):
        self.pairs=[]
        record,target=self.call()
        self.assertEqual(record['reason'],'unsupported_training_features')
        self.assertIsNone(target); self.loader.assert_not_called(); self.judge.assert_not_called()

    def test_pattern_overlap_in_audit_also_blocks_qualification(self):
        duplicate={'uid':'fixture:other','problem_family':'other', 'target':codec.encode(self.row['program'],'fixture'),
                   'pattern_sha256':typed_support.pattern(self.row['program']),'learning_split':'development_audit'}
        self.pairs.append(duplicate)
        record,target=self.call()
        self.assertEqual(record['reason'],'development_overlap')
        self.assertIsNone(target); self.loader.assert_not_called()

    def test_tampered_problem_or_adapter_never_reaches_judge(self):
        self.row['problem_sha256']='changed'
        with self.assertRaisesRegex(ValueError,'source differs'): self.call()
        self.loader.assert_not_called()
        self.row['problem_sha256']=qualification.problem_identity(self.problem)
        self.row['program']['parameters']=['wrong']
        record,target=self.call()
        self.assertEqual(record['reason'],'structural_rejection')
        self.assertIsNone(target); self.judge.assert_not_called()

    def test_failure_keeps_receipt_and_does_not_repair_or_probe(self):
        failed=SimpleNamespace(passed=False, to_dict=lambda:{'passed':False,'tests_passed':0,'first_failure':{'expected':7}})
        self.judge.side_effect=[self.judge.return_value,failed]
        before=copy.deepcopy(self.row)
        record,target=self.call()
        self.assertEqual(record['reason'],'independent_failure'); self.assertIsNone(target)
        self.assertEqual(self.judge.call_count,2); self.assertEqual(self.row,before)
        self.assertNotIn('declared_bound_probe',record)

    def test_qualified_target_is_not_a_training_pair_and_tests_stay_off_source(self):
        record,target=self.call()
        self.assertEqual(record['status'],'qualified')
        self.assertEqual(target['schema'],'algsolve.protected-target.v1')
        self.assertNotIn('learning_split',target); self.assertNotIn('input',target)
        self.assertEqual(self.judge.call_count,3)
        for args,_ in self.judge.call_args_list:
            self.assertNotIn('"expected": 7',args[1])
        self.assertEqual(self.loader.call_count,1)


if __name__=='__main__': unittest.main()
