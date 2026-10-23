"""Synthetic mechanism checks; no corpus measurements."""
import unittest
import search as s


class TailSearchTest(unittest.TestCase):
    def test_mining_uses_distinct_owners_and_excludes_full_bodies(self):
        texts={1:'ababx',2:'abby'}
        labels={str(p):['syntax.operator']*len(t) for p,t in texts.items()}
        pool=s.mine(texts,labels,'syntax',{'abb'},1024)
        self.assertIn('ab',pool)
        self.assertNotIn('aba',pool)  # repeats within one problem do not supply reuse
        self.assertNotIn('abb',pool)

    def test_all_position_proposal_crosses_existing_parse_edge(self):
        texts={1:'abce',2:'zbcd'}
        labels={str(p):['syntax.operator']*len(t) for p,t in texts.items()}
        state={'chosen':{1:'s',2:'s'},'parsed':{(1,'s'):['ab','c','e'],(2,'s'):['zb','c','d']},
               'vocab':['ab','zb','c','e','d']}
        propose=s.occurrence_proposer({'bc':[(1,1,3),(2,1,3)]},lambda *args:[],texts,labels,'syntax')
        self.assertEqual(propose(None,state,10,0),['bc'])

    def test_reclaimed_alphabet_is_not_silently_reinserted(self):
        m=s.module('test_tail_style',s.LIT/'style150-v2/measure.py')
        m.joint.base.ALPHABET=['a','b','c']
        m.v3.FALLBACK={'a','b','c'}
        state=m.joint.evaluate({1:{'s':'ab'},2:{'s':'ac'}},['a','b','c'],7)
        self.assertEqual(state['vocab'],['a','b','c'])
        self.assertEqual(state['selections'],4)

    def test_failed_validation_remains_in_denominator(self):
        rows,illegal=s.evaluate_output({1:'ab',2:'ac'},['a','b'],7,set())
        got=s.aggregate(rows,[1,2],10)
        self.assertEqual(got['problems'],2)
        self.assertEqual(got['covered'],1)
        self.assertEqual(got['failed_ids'],[2])
        self.assertEqual(illegal,[])

    def test_whole_body_is_reported_as_ineligible(self):
        rows,illegal=s.evaluate_output({1:'abab'},['a','b','ab'],7,{'ab'})
        self.assertEqual(illegal,[s.analyze.sha(b'ab')])
        self.assertTrue(rows['1']['encodable'])

    def test_body_extractor_preserves_exact_spelling(self):
        result=s.source_structure({1:'function solve(a){return a+1;}',2:'const solve=a=>a+1;'})
        self.assertIn('return a+1;',result['1']['bodies'])
        self.assertIn('a+1',result['2']['bodies'])
        self.assertEqual(len(result['1']['labels']),len('function solve(a){return a+1;}'))


if __name__=='__main__':
    unittest.main()
