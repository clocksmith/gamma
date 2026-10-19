import ast
import copy
import unittest
from algsolve import semantic_macros as m


class MacroTests(unittest.TestCase):
    def test_both_algorithms_languages_replay_exactly(self):
        for language in m.LANGUAGES:
            for algorithm in ('map','pair_scan'):
                p=m.good_pairs(language,algorithm);data=m.encode(p)
                self.assertEqual(m.decode(data),p)
                self.assertEqual(m.encode(m.decode(data)),data)
                self.assertEqual(m.expand(m.decode(data)),m.expand(p))
                if language=='python':ast.parse(m.expand(p))
                c=m.costs(p)
                self.assertEqual(c['header_bytes']+c['macro_selections']+c['operand_bytes'],len(data))
                self.assertEqual(c['total_binary_presses'],len(data)*8)

    def test_scopes_mutability_types_and_resource_boundaries(self):
        base=m.good_pairs('javascript','map')
        bad=[]
        p=copy.deepcopy(base);p['instructions'][-1]['args']=[{'ref':4}];bad.append(p) # loop local
        p=copy.deepcopy(base);p['instructions'][-1]['args']=[{'ref':1}];bad.append(p) # map return
        p=copy.deepcopy(base);p['instructions'][1]['args'][0]=1;bad.append(p) # shadow map
        p=copy.deepcopy(base);p['instructions'][5]['args'][0]=0;bad.append(p) # input mutation
        p=copy.deepcopy(base);p['instructions'][4]['args'][1]={'ref':1};bad.append(p) # resource arithmetic
        p=copy.deepcopy(base);p['instructions'].pop(-2);bad.append(p) # unclosed loop
        p=copy.deepcopy(base);p['instructions'].append({'op':'end','args':[]});bad.append(p)
        for p in bad:
            with self.subTest(instructions=p['instructions']):
                with self.assertRaises(ValueError):m.encode(p)

    def test_reserved_truncated_tampered_and_noncanonical_streams(self):
        data=m.encode(m.good_pairs('python','map'));header=m.costs(m.good_pairs('python','map'))['header_bytes']
        for bad in [data[:4],data[:-1],data[:header]+bytes([255]),data[:5]+bytes([3])+data[6:],data[:4]+bytes([9])+data[5:],data+bytes([8])]:
            with self.assertRaises(ValueError):m.decode(bad)
        # First literal zero in the var_int entry cannot use an overlong varint.
        i=header+2+3
        self.assertEqual(data[i],0)
        with self.assertRaises(ValueError):m.decode(data[:i]+bytes([128,0])+data[i+1:])

    def test_signed_integer_boundaries_and_boolean_rejection(self):
        for n in (0,1,-1,m.MAX_INTEGER,-m.MAX_INTEGER):
            p=m.good_pairs('python','map');p['instructions'][1]['args'][1]={'int':n}
            self.assertEqual(m.decode(m.encode(p)),p)
        for n in (True,m.MAX_INTEGER+1,-m.MAX_INTEGER-1,1.5):
            p=m.good_pairs('python','map');p['instructions'][1]['args'][1]={'int':n}
            with self.assertRaises(ValueError):m.encode(p)

    def test_method_is_data_not_source_escape(self):
        for name in ('x() {}','for','if','a;process.exit()','é'):
            p=m.good_pairs('javascript','map');p['method']=name
            with self.assertRaises(ValueError):m.encode(p)

    def test_implicit_source_and_unknown_macros_are_rejected(self):
        p=m.good_pairs('python','map');p['instructions'][0]={'op':'source','args':['return 4']}
        with self.assertRaises(ValueError):m.encode(p)
        p=m.good_pairs('python','map');p['instructions'][0]['source']='arbitrary'
        with self.assertRaises(ValueError):m.encode(p)


if __name__=='__main__':unittest.main()
