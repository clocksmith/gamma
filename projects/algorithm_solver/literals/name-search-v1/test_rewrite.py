"""Synthetic binding and exact-cost checks; no development sources."""
import json
import subprocess
import unittest
import rewrite as r


class NameRewriteTests(unittest.TestCase):
    def record(self, text):
        return r.records({'x':text})['x']

    def evaluate(self, text):
        return json.loads(subprocess.check_output(['node','-e',text+';process.stdout.write(JSON.stringify(solve(5)))'],text=True))

    def test_shadowing_global_name_permutation_preserves_links(self):
        text='function solve(a){let x=1;{let x=2;a+=x}return x+a}'
        rec=self.record(text);mapping={x['name']:x['name'] for x in rec['names']};mapping.update(a='x',x='a')
        out=r.render(text,rec,mapping)
        self.assertEqual(self.evaluate(text),self.evaluate(out))

    def test_free_same_spelling_is_never_rewritten(self):
        text='function solve(a){function f(x){return x+a}return x+f(a)}'
        rec=self.record(text)
        self.assertNotIn('x',[n['name'] for n in rec['names']])
        self.assertIn('x',rec['reserved'])

    def test_shorthand_and_entry_excluded_property_key_unchanged(self):
        text='function solve(a){let x=2;let y=3;return {x,key:y}.key+a}'
        rec=self.record(text);mapping={n['name']:n['name'] for n in rec['names']};mapping['y']='z'
        self.assertNotIn('x',mapping); self.assertNotIn('solve',mapping)
        out=r.render(text,rec,mapping)
        self.assertIn('key:z',out);self.assertEqual(self.evaluate(text),self.evaluate(out))

    def test_capture_and_noninjective_maps_rejected(self):
        text='function solve(a){let b=2;return Math.max(a,b)}';rec=self.record(text)
        with self.assertRaises(AssertionError):r.render(text,rec,{'a':'Math','b':'b'})
        with self.assertRaises(AssertionError):r.render(text,rec,{'a':'c','b':'c'})

    def test_dynamic_and_reflection_skip(self):
        for text in ['function solve(a){return eval("a")}', 'function solve(a){return a.name}', 'function solve(a){with(a){return x}}']:
            self.assertEqual(self.record(text)['names'],[])

    def test_exact_improvement_and_semantics(self):
        text='function solve(z){return z+z}'
        vocab=[chr(i) for i in range(32,127)]+['function solve(a){return a+a}']
        # Synthetic entire-source token tests mechanism, never a legal research dictionary.
        out,stats=r.optimize(text,self.record(text),vocab)
        self.assertGreater(stats['moves'],0)
        self.assertLess(len(r.analyze.shortest_encode(out,vocab)),len(r.analyze.shortest_encode(text,vocab)))
        self.assertEqual(self.evaluate(text),self.evaluate(out))

    def test_no_gain_retains_original(self):
        text='function solve(a){return a+1}'
        out,stats=r.optimize(text,self.record(text),[chr(i) for i in range(32,127)])
        self.assertEqual(text,out);self.assertEqual(stats['moves'],0)


if __name__=='__main__':unittest.main()
