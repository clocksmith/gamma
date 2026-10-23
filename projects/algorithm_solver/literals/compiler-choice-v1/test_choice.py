import unittest
import run


class ChoiceTests(unittest.TestCase):
    def test_byte_selection_is_distinct_from_minimum_input(self):
        variants={1:{'original':'aa','standard':'bbbb'}}
        self.assertEqual(run.restrict(variants,'bytes'),{1:{'original':'aa'}})
        m=run.tail.module('compiler_synthetic_style',run.LIT/'style150-v2/measure.py')
        # Whole-program entries are forbidden, so use a shared prefix in larger sources.
        sources={1:{'original':'function solve(){return aa}','standard':'function solve(){return bbbb}'}}
        vocab=[chr(i) for i in range(32,127)]+['\n','bbbb']
        state=m.v3.evaluate(sources,vocab,7,None,m.v3.Budget({'trials':1,'seconds':30}))
        self.assertEqual(state['chosen'][1],'standard')
        self.assertEqual(run.restrict(sources,'control')[1],{'original':sources[1]['original']})

    def test_compilation_retains_original_and_all_profiles(self):
        text='function solve(a){let b=1;let c=2;if(a)return b+c;return b-c}'
        candidates,stats=run.compile_sources({1:text})
        self.assertEqual(candidates[1]['original'],text)
        self.assertEqual(set(candidates[1]),{'original','layout','syntax','standard'})
        self.assertEqual(stats['1']['errors'],{})
        ban=run.forbidden(candidates)
        self.assertTrue(all(t in ban for t in candidates[1].values()))

    def test_reflection_retention_remains_in_denominator(self):
        text='function solve(a){return a.toString()}'
        candidates,stats=run.compile_sources({1:text})
        self.assertEqual(candidates,{1:{'original':text}})
        self.assertEqual(stats['1']['skip'],'reflection_guard')


if __name__=='__main__':unittest.main()
