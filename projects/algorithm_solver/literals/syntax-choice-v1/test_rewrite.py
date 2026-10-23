import unittest
import rewrite as r
ALPHABET=[chr(i) for i in range(32,127)]+['\n']
CFG={'moves':20,'trials':2000,'proposals':256}

class Descent(unittest.TestCase):
    def test_dictionary_cost_can_favor_expansion(self):
        source='function solve(a){let x=a;x+=1;return x}'
        vocab=ALPHABET+['x=x+(1)']
        with r.Client() as c:out,stats=r.optimize(source,vocab,'arithmetic',CFG,c)
        self.assertIn('x=x+(1)',out);self.assertLess(stats['final_selections'],stats['initial_selections'])
        self.assertEqual(stats['accepted'][0]['kind'],'expand_compound')

    def test_flow_dictionary_and_mode_ablation(self):
        source='function solve(a){let x=0;while(x<a){x++;}return x}'
        vocab=ALPHABET+['for(;x<a;)']
        with r.Client() as c:
            out,stats=r.optimize(source,vocab,'flow',CFG,c)
            arithmetic,other=r.optimize(source,vocab,'arithmetic',CFG,c)
        self.assertIn('for(;x<a;)',out);self.assertNotIn('for(',arithmetic)
        self.assertLess(stats['final_selections'],stats['initial_selections'])

    def test_exact_trial_cap_and_nonincrease(self):
        source='function solve(a){let x=a;x++;x--;x+=2;return x}'
        with r.Client() as c:out,stats=r.optimize(source,ALPHABET,'combined',{**CFG,'trials':1},c)
        self.assertEqual(stats['trials'],1);self.assertEqual(stats['stop'],'trial_limit')
        self.assertLessEqual(stats['final_selections'],stats['initial_selections'])

    def test_unsupported_reflection_unchanged(self):
        source='function solve(a){return solve.toString()}'
        with r.Client() as c:out,stats=r.optimize(source,ALPHABET,'combined',CFG,c)
        self.assertEqual(out,source);self.assertTrue(stats['unsupported']);self.assertEqual(stats['trials'],0)

if __name__=='__main__':unittest.main()
