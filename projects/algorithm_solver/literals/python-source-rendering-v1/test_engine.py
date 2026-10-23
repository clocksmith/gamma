"""Matched supplied-source controls and exact codec ties; invented data only."""
import copy
import unittest
import engine
import render

ALPHABET=[chr(i) for i in range(32,127)]+['\n']


class EngineTests(unittest.TestCase):
    def test_unchanged_wins_exact_source_cost_tie(self):
        original='def solve(x): return x + 1\n'
        alternate='def solve(x):return  x + 1\n'
        render.validate(original,alternate)
        self.assertEqual(len(original),len(alternate))
        groups={'p':engine.normalized(original,[alternate,original])}
        chosen,trace=engine.choose({'p':original},groups,ALPHABET,7)
        self.assertEqual(chosen['p'],original)
        self.assertTrue(trace['p']['unchanged'])
        state=engine.parent.v3.evaluate(groups,ALPHABET,7,None,engine.parent.v3.Budget({'seconds':10,'trials':1}))
        self.assertEqual(groups['p'][state['chosen']['p']],original)

    def test_factorial_arms_hold_dictionary_and_source_controls(self):
        texts={'a':'class Solution:\n    def solve(self,n):\n        value = n + 1\n        return value\n',
               'b':'class Solution:\n    def solve(self,n):\n        value = n + 2\n        return value\n'}
        cfg={'rounds':2,'search':{'trials':1,'seconds':10},
             'neighborhood':{'additions':96,'swaps':500,'pairs':150,'pair_additions':16,'pair_removals':8,'designed_fraction':.25}}
        fit=engine.fit_supplied(texts,ALPHABET,7,{p:'solve' for p in texts},cfg)
        self.assertEqual(set(fit['arms']),set(engine.ARMS))
        self.assertFalse(fit['validation_loaded']);self.assertFalse(fit['case_data_loaded'])
        self.assertEqual(fit['arms']['U']['fit_sources'],texts)
        self.assertEqual(fit['arms']['D']['fit_sources'],texts)
        for name,arm in fit['arms'].items():
            self.assertEqual(arm['dictionary'],ALPHABET)
            self.assertEqual(len(arm['search']),2 if name in ('D','J') else 1)
            self.assertTrue(all(row['trials']==1 for row in arm['search']))
            for p,text in arm['fit_sources'].items():
                render.validate(texts[p],text)
                seq=engine.parent.analyze.shortest_encode(text,arm['dictionary'])
                packet=engine.parent.analyze.encode(arm['dictionary'],seq,7)
                self.assertEqual(engine.parent.analyze.decode(engine.parent.analyze.dictionary_bytes(arm['dictionary']),packet),text)
        self.assertLess(fit['arms']['S']['fit_selections'],fit['arms']['U']['fit_selections'])
        self.assertEqual(fit['arms']['J']['fit_sources'],fit['arms']['S']['fit_sources'])
        sealed={a:list(row['dictionary']) for a,row in fit['arms'].items()};before=copy.deepcopy(sealed)
        validation,_=engine.validation_supplied(texts,sealed,7)
        self.assertEqual(sealed,before)
        self.assertEqual(validation['U']['sources'],texts)
        self.assertEqual(validation['D']['sources'],texts)
        self.assertEqual(validation['S']['sources'],fit['arms']['S']['fit_sources'])

    def test_complete_python_bodies_are_banned_for_all_menu_variants(self):
        texts={'a':'class Solution:\n    def solve(self,n):\n        return n + 1\n',
               'b':'class Solution:\n    def solve(self,n):\n        return n + 2\n'}
        groups,_=engine.source_menus(texts)
        banned=engine.parent.banned(groups,{p:'solve' for p in texts})
        for choices in groups.values():
            for text in choices.values():
                self.assertIn(text,banned)
        self.assertIn('return n+1',banned)

    def test_source_choice_scores_canonical_actions_not_byte_shortness(self):
        original='def solve(x): return x + 1\n'
        compact='def solve(x):return x+1\n'
        vocab=ALPHABET+['def solve(x): return x + ']
        groups={'p':engine.normalized(original,[original,compact])}
        chosen,_=engine.choose({'p':original},groups,vocab,7)
        self.assertEqual(chosen['p'],original)
        self.assertLess(len(compact),len(original))


if __name__=='__main__':unittest.main()
