"""Deterministic import/qualification boundary tests, not solving evidence."""
import unittest
from types import SimpleNamespace

from algsolve.records import Problem, LANE_ROOT
from algsolve.synth import typed_codec
from algsolve.synth.prepare_typed_suby import development_boundary, qualify


class NewDevelopmentPreparation(unittest.TestCase):
    def test_metadata_excludes_solving_recognition_aliases_before_payload_access(self):
        manifest={'solving':{'held':['lcd:1']},'recognition':[{'target':'lc:recognition'}],
                  'recognition_dev':[], 'near_duplicates':{'dropped_index_entries':['lc:removed'],
                  'sibling_pairs_kept':[{'index_key':'lc:alias','pool_uid':'lcd:1'}]}}
        catalog={'excluded':{'lc:secret-ii':'protected_composition_alias'}}
        reservation={'reservation':{'pool':[{'key':'lc:reserved','family':'reserved','members':['lcd:8']}]}}
        metadata=[{'task_id':'held','question_id':1},{'task_id':'held-ii','question_id':2},
                  {'task_id':'alias','question_id':3},{'task_id':'recognition-iii','question_id':4},
                  {'task_id':'allowed','question_id':5}]
        limits=development_boundary(metadata,manifest,catalog,reservation)
        self.assertTrue({'lcd:1','lcd:2','lcd:3','lcd:4','lcd:8'}<=set(limits['uids']))
        self.assertNotIn('lcd:5',limits['uids']);self.assertIn('secret',limits['families'])

    def fixture(self):
        identity=typed_codec.frozen(LANE_ROOT/'contracts/typed_codec_v1.json')
        graph={'schema':'algsolve.typed-program.v2','parameters':['values'],'inputs':{'values':['list','int']},
               'body':[],'return':{'op':'len','args':[{'ref':'values'}]},'output_type':'int'}
        proposal={'uid':'lcd:fixture','variant':'length','program':graph,'requirements':{'unsupported_requirements':[]},
                  'bound_probe':{'args':[[1,2]],'expected':2},'proposer':'synthetic-development-test'}
        problem=Problem('lcd:fixture','lcd','fixture','','','Count values.','functional',
                        entry={'class':'Solution','method':'length'},params=[['values','List[int]']],
                        public_tests=[{'args':[[1]],'expected':1}])
        entry=SimpleNamespace(key='lc:anonymous',slug='anonymous',license=['fixture'],attribution=['fixture'])
        return proposal,problem,entry,identity

    def test_qualified_label_needs_all_three_execution_gates(self):
        proposal,problem,entry,identity=self.fixture();calls=[]
        def judge(p,code,cases):
            self.assertIn('def length',code);calls.append(cases)
            return SimpleNamespace(to_dict=lambda:{'passed':True,'tests_passed':len(cases),'reason':'passed'})
        tests=[{'args':[[1,2,3]],'expected':3}]
        pair,record=qualify(proposal,problem,tests,entry,identity,judge=judge)
        self.assertEqual(record['reason'],'qualified');self.assertEqual(len(calls),3)
        self.assertEqual(pair['input']['public_examples'],problem.public_tests)
        self.assertNotIn('independent_tests',pair['input'])
        self.assertEqual(pair['provenance']['independent_tests_passed'],1)

    def test_independent_failure_retained_and_bound_not_executed(self):
        proposal,problem,entry,identity=self.fixture();calls=[]
        def judge(*args):
            calls.append(1);ok=len(calls)==1
            return SimpleNamespace(to_dict=lambda:{'passed':ok,'tests_passed':int(ok),'reason':'passed' if ok else 'wrong_answer'})
        pair,record=qualify(proposal,problem,[{'args':[[1]],'expected':1}],entry,identity,judge=judge)
        self.assertIsNone(pair);self.assertEqual(record['reason'],'qualification_failed')
        self.assertEqual(len(calls),2);self.assertEqual(record['verdicts']['independent']['reason'],'wrong_answer')

    def test_missing_examples_and_unsupported_requirements_do_not_execute(self):
        proposal,problem,entry,identity=self.fixture()
        def forbidden(*args):raise AssertionError('judge must not run')
        problem.public_tests=[]
        self.assertEqual(qualify(proposal,problem,[{}],entry,identity,judge=forbidden)[1]['reason'],'missing_public_or_independent_tests')
        proposal['requirements']['unsupported_requirements']=['out_of_scope']
        self.assertEqual(qualify(proposal,problem,[{}],entry,identity,judge=forbidden)[1]['reason'],'unsupported_requirements')

if __name__=='__main__':unittest.main()
