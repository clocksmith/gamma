"""Focused checks for palette-names-v1: palette construction, cost-guided multi-character names, capture safety."""
import sys, unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent)]
import palette
from palette import rewrite

ALPHA = [chr(i) for i in range(32, 127)] + ['\n']


class Palette(unittest.TestCase):
    def test_palette_order_exclusions_and_owners(self):
        vocab = ALPHA + ['count', 'let', 'await', 'Math', 'x+1', 'solve', 'idx']
        recs = {1: {'variables': [{'name': 'total'}, {'name': 'tmp'}]}, 2: {'variables': [{'name': 'total'}]}}
        names = palette.build_palette(vocab, recs, 40, 12)
        self.assertEqual(names, ['count', 'idx', 'total'])  # learned identifier entries longest first, then shared fit names
        self.assertLessEqual(len(palette.build_palette(vocab, recs, 1, 12)), 1)

    def test_palette_name_lowers_exact_cost_when_a_z_cannot(self):
        text = 'function solve(a){let q=0;for(let i=0;i<a.length;i++){q+=a[i];}return q;}'
        vocab = ALPHA + ['total+=a[i];', 'return total;']
        rec = rewrite.records({'p': text})['p']
        az, s1 = palette.optimize(text, rec, vocab, list('abcdefghijklmnopqrstuvwxyz'), 2, 6000)
        pal, s2 = palette.optimize(text, rec, vocab, list('abcdefghijklmnopqrstuvwxyz') + ['total'], 2, 6000)
        tree = rewrite.codec.trie(vocab); cost = lambda t: len(rewrite.codec.encode_text(t, tree))
        self.assertLess(cost(pal), cost(az))
        self.assertIn('total+=a[i];', pal)
        self.assertEqual(s2['multichar_names_introduced'], 1)

    def test_palette_name_never_captures_an_unresolved_reference(self):
        text = 'function solve(a){let q=0;q+=total(a);return q;}'  # `total` is an unresolved (global) reference
        vocab = ALPHA + ['total+=', 'return total;']
        rec = rewrite.records({'p': text})['p']
        out, _ = palette.optimize(text, rec, vocab, ['total'], 2, 6000)
        self.assertNotIn('let total', out)

    def test_unsafe_program_is_unchanged(self):
        text = 'function solve(a){let q=eval("1");return q;}'
        rec = rewrite.records({'p': text})['p']
        out, s = palette.optimize(text, rec, ALPHA + ['total'], ['total'], 2, 6000)
        self.assertEqual((out, s['stop']), (text, 'unsupported'))


if __name__ == '__main__':
    unittest.main()
