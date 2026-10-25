import itertools
import unittest
from fractions import Fraction
import frontier as f


class ExactControls(unittest.TestCase):
    def test_00_dual_only_padding_regression(self):
        # Zero potentials satisfy every unit-cost dual inequality. This is NOT
        # primal equality and cannot turn a claimed eight-selection path into <=3.
        d = ('a','b','ab')
        self.assertTrue(all(0 <= 0+1 for _ in d))
        self.assertFalse(f.verify_claim('ab',d,[2],8,3))
        self.assertFalse(f.verify_claim('ab',d,[0,1],2,3))
        self.assertFalse(f.verify_claim('ab',d,[2]*8,8,3))
        self.assertTrue(f.verify_claim('ab',d,[2],1,3))

    def test_source_choice_crossover(self):
        variants = {'p': {'left':'aaaa','right':'bbbbbb'}}
        a = f.solve(variants,('a','aa','b'),16)['best']
        b = f.solve(variants,('a','b','bb'),16)['best']
        self.assertEqual(a['selected']['p'][0],'left')
        self.assertEqual(b['selected']['p'][0],'right')

    def test_joint_gate_requires_nonlocal_source_choice(self):
        v = {'p': {'short':'aaa','long':'cccccccc'}}
        result = f.solve(v,('a','aa','cc'),16,max_character_fraction=0)
        self.assertEqual(result['best']['selected']['p'][0],'long')
        self.assertEqual(result['best']['metrics']['selections'],4)

    def test_unreachable_is_none_and_denominator_retained(self):
        self.assertIsNone(f.exact_path('ab',('a',)))
        result = f.solve({'a':{'v':'aaaa'},'b':{'v':'bbbb'}},('aa',),16,minimum_coverage=1)
        self.assertEqual(result['best']['unreachable'],('b',))
        self.assertEqual(result['best']['metrics']['denominator'],2)

    def test_character_retirement_no_mandatory_alphabet(self):
        result = f.solve({'p':{'v':'aaaa'}},('a','aa'),16)
        self.assertEqual(result['best']['dictionary'],('aa',))
        self.assertEqual(result['best']['metrics']['characters'],0)

    def test_unicode_actual_singleton_not_id_or_utf8_bytes(self):
        self.assertEqual(f.exact_path('éé🙂',('éé','🙂'))[:2],(2,1))

    def test_even_median_exact(self):
        self.assertEqual(f.median([1,64]),Fraction(65,2))
        self.assertGreater(f.median([1,64]),32)
        self.assertEqual(f.median([1,3,99]),3)

    def test_even_median_gate_end_to_end(self):
        v = {'p':{'v':'aa'},'q':{'v':'b'*63}}
        no = f.solve(v,('a','b'),16,max_median=32)
        yes = f.solve(v,('a','b'),16,max_median=Fraction(65,2))
        self.assertEqual(no['status'],'infeasible_finite_U_V')
        self.assertEqual(yes['best']['metrics']['median'],Fraction(65,2))

    def test_whole_source_exclusion_includes_unselected(self):
        result = f.solve({'p':{'a':'abab','b':'ab'}},('ab','a','b'),16)
        self.assertEqual(result['excluded_whole_sources'],1)
        self.assertNotIn('ab',result['best']['dictionary'])

    def test_infeasibility_is_finite_only_and_budget_is_incomplete(self):
        result = f.solve({'p':{'v':'ab'}},('a',),16)
        self.assertEqual(result['status'],'infeasible_finite_U_V')
        self.assertFalse(result['best'])
        cut = f.solve({'p':{'v':'abab'}},('a','b','ab'),16,max_evaluations=1)
        self.assertEqual(cut['status'],'incomplete_budget')
        self.assertFalse(cut['complete'])

    def test_full_cost_and_profiles_packet_reconstruction(self):
        v = {'p':{'v':'éééé'},'q':{'v':'éééééé'}}
        for capacity in f.PROFILES:
            row = f.solve(v,('é','éé'),capacity)['best']
            m = row['metrics']
            self.assertEqual(m['width'],capacity.bit_length()-1)
            self.assertEqual(m['selection_bits'],5*m['width'])
            self.assertEqual(m['dictionary_bytes'],8+4+len('éé'.encode()))
            self.assertEqual(m['packet_bytes'],82+(2*m['width']+7)//8+(3*m['width']+7)//8)
            self.assertEqual(m['package_bytes'],m['dictionary_bytes']+m['packet_bytes']+m['decoder_bytes'])

    def test_systematic_expansion_and_merge_complete(self):
        v = {'p':{'v':'ababa'},'q':{'v':'babab'}}
        levels = list(f.expansion_levels(v,3))
        self.assertEqual(set(levels[0]),{'a','b'})
        self.assertEqual(set(levels[1]),{'a','b','ab','ba'})
        self.assertEqual(set(levels[2]),{'a','b','ab','ba','aba','bab'})
        totals = [f.solve(v,u,16)['best']['metrics']['selections'] for u in levels]
        self.assertEqual(totals,[10,6,4])

    def test_exhaustive_independent_segmentation_oracle(self):
        # All binary strings through length five, all subsets of a tiny U.
        universe = ('a','b','aa','ab','ba','bb')
        def paths(source,d):
            if not source:
                yield (0,0,())
            for i,s in enumerate(d):
                if source.startswith(s):
                    for n,c,ids in paths(source[len(s):],d):
                        yield n+1,c+(len(s)==1),(i,)+ids
        for size in range(1,7):
            for d in itertools.combinations(universe,size):
                for length in range(1,6):
                    for chars in itertools.product('ab',repeat=length):
                        text = ''.join(chars)
                        all_paths = list(paths(text,d))
                        expected = min(all_paths) if all_paths else None
                        self.assertEqual(f.exact_path(text,d),expected)

    def test_independent_joint_dictionary_source_oracle(self):
        v = {'p':{'a':'ababa','b':'aaaaaa'},'q':{'a':'babab','b':'bbbbbb'}}
        u = ('a','b','aa','bb','ab','ba')
        result = f.solve(v,u,16)
        oracle = []
        for size in range(1,len(u)+1):
            for d in itertools.combinations(u,size):
                pairs = [[f.exact_path(s,d) for s in rows.values()] for rows in v.values()]
                for paths in itertools.product(*pairs):
                    if all(p is not None for p in paths):
                        oracle.append((sum(p[0] for p in paths),sum(p[1] for p in paths)))
        m = result['best']['metrics']
        self.assertEqual((m['selections'],m['characters']),min(oracle))
        self.assertEqual(result['dictionaries'],2**len(u)-1)

    def test_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            f.solve({'p':{'v':'abc'}},('a','a'),16)
        with self.assertRaises(ValueError):
            f.solve({'p':{'v':'abc'}},('a',),15)


if __name__ == '__main__':
    unittest.main()
