import importlib.util
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('python_systematic_search',HERE/'search.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

class SearchTests(unittest.TestCase):
    def texts(self):
        return {'1:a':'def solve(values):\n    count = 0\n    for value in values:\n        count += value\n    return count\n','2:a':'def solve(values):\n    count = 1\n    for value in values:\n        count *= value\n    return count\n'}
    def builder(self,capacity=128):
        t=self.texts();owners={k:k.split(':')[0] for k in t};refs={v:k for k,v in owners.items()};return s.Builder(t,owners,refs,{p:'sequence-loop' for p in refs},capacity=capacity)
    def test_python_whole_body_excluded(self):
        b=self.builder();self.assertFalse(b.legal(self.texts()['1:a']));self.assertFalse(b.legal('count = 0\n    for value in values:\n        count += value\n    return count'))
        self.assertTrue(b.legal('    for value in values:\n'))
    def test_source_structure_family(self):
        self.assertEqual(s.family(self.texts()['1:a']),'sequence-loop')
        self.assertEqual(s.family('def solve(node):\n    return node.next\n'),'linked-node')
    def test_full_worklist_bound_equivalence(self):
        b=self.builder();state=b.score(['1','2'],[]);one,stats=b.best_move(state);two,_=b.best_move(state,prune=False)
        self.assertEqual(one[0:3],two[0:3]);self.assertEqual(one[3]['choices'],two[3]['choices']);self.assertGreater(stats['worklist'],0)
    def test_codec_exact_python_indentation(self):
        b=self.builder();state=b.score(['1','2'],[]);v=s.ALPHABET+state['learned'];summary,artifacts=s.joint.compare.measure({p:b.texts[k] for p,k in state['choices'].items()},v,7)
        self.assertEqual(summary['selections'],state['metrics']['selections']);self.assertEqual(len(artifacts['packets']),2)
    def test_unicode_fail_closed(self):
        with self.assertRaises(ValueError):s.Builder({'x':'def solve():\n    return "é"\n'},{'x':'1'},{'1':'x'},{'1':'other'},capacity=128)

if __name__=='__main__':unittest.main()
