import unittest
from search import Builder, ALPHABET, digest, dominates

class IncrementalTests(unittest.TestCase):
    def builder(self):
        texts={'a':'function solve(a){return a+1;}', 'b':'function solve(a){return a+2;}',
               'a2':'function solve(a){let b=1;return a+b;}'}
        return Builder(texts,{'a':'1','b':'2','a2':'1'},{'1':'a','2':'b'},
                       {'1':'arithmetic','2':'arithmetic'},capacity=128)
    def test_distinct_problem_support(self):
        b=self.builder();self.assertFalse(b.legal('let b=1;'));self.assertTrue(b.legal('function solve(a){'))
    def test_whole_body_and_wrapper_rejected(self):
        b=self.builder();self.assertFalse(b.legal('return a+1;'));self.assertFalse(b.legal('{return a+1;}'))
    def test_growth_chain_reconstruction(self):
        b=self.builder();s=b.grow(['1','2'],slots=3)
        self.assertLess(s['metrics']['selections'],60)
        self.assertEqual(len(s['learned']),3)
        prior='0'*64
        for event in b.events:
            self.assertEqual(event['previous_sha256'],prior)
            saved=dict(event);prior=saved.pop('sha256');self.assertEqual(digest(saved),prior)
        for pid,key in s['choices'].items():self.assertEqual(''.join(s['selected'][pid]['used']),b.texts[key])
    def test_capacity(self):
        with self.assertRaises(ValueError):self.builder().score(['1','2'],['x'*n for n in range(2,40)])
    def test_frontier(self):
        m={'entries':100,'above96':1,'above32':2,'character_excess':10,'selections':50,'characters':6,'literal_utf8_bytes':120}
        n={**m,'selections':60};self.assertTrue(dominates(m,n));self.assertFalse(dominates(n,m))

if __name__=='__main__':unittest.main()
