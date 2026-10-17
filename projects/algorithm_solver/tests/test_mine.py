import ast
import unittest
from types import SimpleNamespace
from algsolve.synth.mine import mine, normalized, reserve


def entry(key, code='', difficulty='Easy'):
    return SimpleNamespace(key='lc:'+key, slug=key, difficulty=difficulty, judge_uid='test:'+key,
        references=[{'code':code,'validated':True,'uid':key}], license=['fixture'], attribution=['fixture'])

class MiningTests(unittest.TestCase):
    def test_alpha_renaming_keeps_operators_constants_and_global_names(self):
        norm = lambda text: normalized(ast.parse(text).body[0])
        self.assertEqual(norm('def f(x):\n y=x+1\n return y'), norm('def g(a):\n b=a+1\n return b'))
        self.assertNotEqual(norm('def f(x): return x+1'), norm('def f(x): return x+2'))
        self.assertNotEqual(norm('def f(x): return min(x)'), norm('def f(x): return max(x)'))

    def test_clustering_preserves_provenance_and_skips_unvalidated_references(self):
        first = entry('first', 'def f(x): return x+1')
        second = entry('second', 'def g(a): return a+1')
        third = entry('third', 'def g(a): return a+1')
        third.references[0]['validated'] = False
        clusters, failures = mine([first, second, third])
        self.assertEqual(failures,0)
        self.assertEqual(len(clusters),1)
        self.assertEqual(clusters[0]['family_count'],2)
        self.assertEqual({p['key'] for p in clusters[0]['provenance']}, {'lc:first','lc:second'})

    def test_confirmation_reserves_whole_families_and_excludes_development(self):
        entries = [entry('robber'),entry('robber-ii'),entry('stock'),entry('stock-ii'),entry('single')]
        chosen = reserve(entries, {'lc:robber'}, 2, 42)
        self.assertEqual(set(chosen), {'lc:stock','lc:stock-ii','lc:single'})
        with self.assertRaises(ValueError): reserve(entries, {'lc:robber'}, 3, 42)

if __name__ == '__main__': unittest.main()
