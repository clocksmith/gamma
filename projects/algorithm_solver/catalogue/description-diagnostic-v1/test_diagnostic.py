import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location('description_diagnostic', pathlib.Path(__file__).with_name('run_diagnostic.py'))
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)

class Service:
    def __init__(self): self.calls=[]
    def request(self, ident, *, include_source):
        assert include_source is False
        self.calls.append(ident)
        return {'status': 'matched', 'problem_id': ident}

class DiagnosticTests(unittest.TestCase):
    def test_tie_order_is_identity_not_coverage(self):
        self.assertEqual(d.rank([.5,.5], ['b','a']), [('a',.5),('b',.5)])
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError): d.rank([float('nan')], ['a'])
    def test_top_one_never_accepts(self):
        q={'query_id':'p','kind':'positive','expected_ids':['a']}; s=Service()
        r=d.outcome(q,[('a',1.)],s,truncated=False)
        self.assertEqual(r['status'],'abstain'); self.assertEqual(r['expected_rank'],1)
        self.assertTrue(r['unknown_interpretation_retained']); self.assertIsNone(r['accepted_answer'])
        self.assertEqual(s.calls,['a'])
    def test_truncation_blocks_even_metadata(self):
        s=Service(); r=d.outcome({'query_id':'x','kind':'positive'}, [('a',1.)],s,truncated=True)
        self.assertEqual(r['reason'],'truncation'); self.assertEqual(s.calls,[]); self.assertEqual(r['rankings'],[])
    def test_absent_control_does_not_get_positive_metric(self):
        r=d.outcome({'query_id':'x','kind':'absent_from_pilot'}, [('a',.99)],Service(),truncated=False)
        self.assertNotIn('expected_rank',r); self.assertEqual(r['status'],'abstain')

if __name__ == '__main__': unittest.main()
