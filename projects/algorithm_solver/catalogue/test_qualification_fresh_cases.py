import unittest
from .qualification_fresh_cases import expected, validate, build, IDS
from . import imported_qualification as runner
from .verify_imported_qualification import independent_failures


class FreshOracleTests(unittest.TestCase):
    def test_definition_examples(self):
        self.assertEqual(expected(301, ['()())()']), ['(())()', '()()()'])
        self.assertEqual(expected(1799, [[3,4,6,8]]), 11)
        self.assertEqual(expected(1830, ['cba']), 5)
        self.assertEqual(expected(2514, ['too hot']), 18)
        self.assertEqual(expected(2954, [5,[0,4]]), 4)
        self.assertEqual(expected(2963, [[1,2,3,4]]), 8)
        self.assertEqual(expected(3697, [537]), [500,30,7])
        self.assertEqual(expected(3827, [4]), 3)
        self.assertEqual(expected(3870, [1000]), 1)

    def test_domain_rejections(self):
        for pid,args in [(3516,[True,2,3]),(3536,[9]),(3560,[4,4,2]),(3606,[['x'],['grocery'],[1]]),
                         (3643,[[[1]],0,0,2]),(3668,[[1,2],[2,1]]),(3731,[[1,1]]),
                         (3875,[[1,1]]),(2612,[5,0,[0],1]),(2954,[3,[0,0]]),
                         (3940,[[2,1],1]),(3823,['a1']),
                         (3606,['a','b',[True]]),(3838,['abc',[1]*26])]:
            with self.assertRaises(ValueError, msg=str(pid)):
                validate(pid,args)

    def test_generated_cases_all_meet_statement_domains(self):
        cases=build();self.assertEqual(set(cases),set(IDS))
        for pid,rows in cases.items():
            self.assertTrue(rows)
            for row in rows:validate(pid,row['args'])

    def test_order_policy_is_explicit_and_preserves_multiplicity(self):
        case={'args':['()())()'],'expected':['(())()','()()()']}
        obs={'i':0,'result':['()()()','(())()'],'result_type':'list','args_before':case['args'],'args_after':case['args'],'alias_edges':[]}
        self.assertEqual(runner.compare(case,obs,'python'),'result_value')
        self.assertIsNone(runner.compare(case,obs,'python','set-of-strings'))
        raw=runner.encoded(obs)+runner.encoded({'done':1})
        self.assertEqual(independent_failures(raw,[case],'python','set-of-strings'),[])
        obs['result'].append('()()()')
        self.assertEqual(runner.compare(case,obs,'python','set-of-strings'),'result_value')
        self.assertTrue(independent_failures(runner.encoded(obs)+runner.encoded({'done':1}),[case],'python','set-of-strings'))


if __name__=='__main__':unittest.main()
