import unittest
import run


class ScopeChoiceTests(unittest.TestCase):
    def test_matched_printer_and_default_controls(self):
        variants={1:{'original':'old','layout':'printed','default':'auto','rotate00':'fixed'}}
        self.assertEqual(set(run.restrict(variants,'control')[1]),{'original','layout'})
        self.assertEqual(set(run.restrict(variants,'default')[1]),{'original','layout','default'})
        self.assertEqual(run.restrict(variants,'select'),variants)

    def test_binding_metadata_and_original_retention(self):
        text='function solve(input){function first(longOne){return longOne+1}function second(longTwo){return longTwo*2}return first(input)+second(input)}'
        candidates,stats=run.compile_sources({1:text})
        self.assertEqual(candidates[1]['original'],text);self.assertEqual(len(candidates[1]),12)
        self.assertEqual(stats['1']['errors'],{})
        b=stats['1']['binding_stats'];self.assertEqual(b['original']['bindings'],b['rotate00']['bindings'])
        self.assertLess(b['rotate00']['distinct_spellings'],b['original']['distinct_spellings'])

    def test_skips_remain_in_all_controls(self):
        text='function solve(a){return a.toString()}'
        variants,stats=run.compile_sources({1:text})
        self.assertEqual(stats['1']['skip'],'reflection_guard')
        for arm in ('control','default','select','joint'):self.assertEqual(run.restrict(variants,arm),{1:{'original':text}})


if __name__=='__main__':unittest.main()
