import sys
from pathlib import Path
import unittest
import bindings
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'name-search-v1'))
import rewrite


class PythonBindingTests(unittest.TestCase):
    def value(self,text):
        ns={};exec(text,ns);return ns['Solution']().solve(5)

    def test_local_swap_and_property_preservation(self):
        text='class Solution:\n def solve(self,a):\n  x=2\n  return a+x\n'
        r=bindings.record(text);mapping={n['name']:n['name'] for n in r['names']};mapping.update(a='x',x='a')
        out=rewrite.render(text,r,mapping)
        self.assertEqual(self.value(text),self.value(out));self.assertIn('def solve(self,',out)

    def test_free_and_global_spelling_excluded(self):
        text='class Solution:\n def solve(self,a):\n  x=2\n  def f():return x\n  return f()+a\n'
        self.assertNotIn('x',[n['name'] for n in bindings.record(text)['names']])

    def test_keyword_parameter_and_reflection(self):
        text='class Solution:\n def solve(self,a):\n  def f(x):return x\n  return f(x=a)\n'
        self.assertNotIn('x',[n['name'] for n in bindings.record(text)['names']])
        self.assertEqual(bindings.record('def f(a): return locals()')['names'],[])

    def test_exception_match_and_import_bindings_reserved(self):
        text='def f(a):\n import math as m\n try: return a\n except Exception as e: return str(e)\n'
        r=bindings.record(text)
        self.assertTrue({'m','e'}<=set(r['reserved']))

    def test_capture_prevention(self):
        text='def f(a): return a+len([])\n';r=bindings.record(text)
        with self.assertRaises(AssertionError):rewrite.render(text,r,{'a':'len'})

    def test_dictionary_aware_rewrite_preserves_value(self):
        text='class Solution:\n def solve(self,z):return z+z\n'
        vocab=[chr(i) for i in range(32,127)]+['\n','return a+a']
        out,stats=rewrite.optimize(text,bindings.record(text),vocab)
        self.assertGreater(stats['moves'],0);self.assertEqual(self.value(text),self.value(out))

    def test_entry_exclusion_and_unicode_skip(self):
        text='class Solution:\n def solve(self,a):return a+1\n'
        banned=bindings.forbidden(text,'solve')
        self.assertIn('return a+1',banned);self.assertIn(text,banned)
        self.assertTrue(bindings.record('def f(é): return é')['unsafe'])

    def test_unicode_body_uses_ast_byte_positions(self):
        text='class Solution:\n def solve(self,a):return "é"+a\n'
        self.assertIn('return "é"+a',bindings.forbidden(text,'solve'))


if __name__=='__main__':unittest.main()
