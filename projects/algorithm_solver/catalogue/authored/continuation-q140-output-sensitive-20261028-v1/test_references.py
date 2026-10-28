"""Independent reference/certificate controls only; never import a candidate."""
import importlib.util
from pathlib import Path
import unittest
S=importlib.util.spec_from_file_location('q140_new_case_controls',Path(__file__).with_name('cases.py'))
cases=importlib.util.module_from_spec(S);S.loader.exec_module(cases)

class ReferenceControls(unittest.TestCase):
    def test_dense_suffix_zero_answer_certificate(self):
        words=['a'*size for size in range(1,11)]
        for suffix_length in range(11):
            args=['b'+'a'*suffix_length,words]
            self.assertEqual(cases.unreachable_prefix_certificate(args),cases.reference.reference(140,args))
        self.assertEqual(cases.unreachable_prefix_certificate(['b'+'a'*19,words]),[])
    def test_certificate_cannot_claim_feasible_start(self):
        with self.assertRaises(ValueError):cases.unreachable_prefix_certificate(['aa',['a','aa']])
    def test_inherited_cases_and_memberships_unchanged(self):
        original=cases.generator.build_cases(140,include_maximum=True);new=cases.build_cases()
        self.assertEqual(len(new),len(original)+1)
        for index,(old,row) in enumerate(zip(original,new)):
            self.assertEqual({key:value for key,value in row.items() if key!='inherited_q_case_index'},old)
            self.assertEqual(row['inherited_q_case_index'],index)
        self.assertEqual(new[-1]['args'][0],'b'+'a'*19);self.assertEqual(new[-1]['expected'],[])
    def test_reference_complete_distinct_answers(self):
        args=['catsanddog',['cat','cats','and','sand','dog']]
        self.assertEqual(set(cases.reference.reference(140,args)),{'cat sand dog','cats and dog'})
        self.assertEqual(cases.reference.reference(140,['aa',['a','aa']]),['a a','aa'])

if __name__=='__main__':unittest.main()
