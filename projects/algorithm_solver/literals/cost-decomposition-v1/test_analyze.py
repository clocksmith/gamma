"""Focused mathematical and attribution checks on synthetic text only."""
from itertools import combinations
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import analyze as a


class BoundsTest(unittest.TestCase):
    def test_suffix_matches_brute_force(self):
        sources = {1: 'ababa', 2: 'babcab', 3: 'ababa', 4: 'ddca'}
        got = a.shared_lengths(sources)
        for pid, text in sources.items():
            want = [max([1] + [k for k in range(1, len(text) - i + 1)
                    if any(text[i:i+k] in other for p, other in sources.items() if p != pid)])
                    for i in range(len(text))]
            self.assertEqual(got[pid], want)

    def test_capacity_certificate_against_every_tiny_dictionary(self):
        sources = {1: 'abab', 2: 'baba', 3: 'acac', 4: 'ccbb'}
        strings = sorted({t[i:j] for t in sources.values() for i in range(len(t))
                          for j in range(i+1, len(t)+1)} - set(sources.values()))
        lengths = a.shared_lengths(sources)
        base = [a.relaxed_count(t, lengths[p]) for p, t in sources.items()]
        feasible = 0
        for cap in (2, 3, 4):
            lower = sorted(a.capacity_bound(base, cap))
            for vocab in combinations(strings, cap):
                try:
                    counts = sorted(len(a.shortest_encode(t, list(vocab))) for t in sources.values())
                except ValueError:
                    continue
                feasible += 1
                self.assertTrue(all(lo <= hi for lo, hi in zip(lower, counts)))
        self.assertGreater(feasible, 0)

    def test_transfer_oracle_matches_brute(self):
        fit = {1: 'abcdef', 2: 'abbc'}
        target = {3: 'abqdef', 4: 'cababbc'}
        got = a.fit_oracle(fit, target)
        vocab = sorted({t[i:j] for t in fit.values() for i in range(len(t)) for j in range(i+1, len(t)+1)}
                       | set(''.join(target.values())))
        for pid, text in target.items():
            self.assertEqual(got[pid], max(2, len(a.shortest_encode(text, vocab))))

    def test_mixed_selection_and_single_tail_conserve_cost(self):
        got = a.attribute('a+12', ['a+', '1', '2'], [0, 1, 2], ['identifier', 'syntax.operator', 'literal', 'literal'])
        self.assertEqual(got['fractional_selections'], {'identifier': .5, 'syntax.operator': .5, 'literal': 2})
        self.assertEqual(got['exclusive_selections'], {'mixed': 1, 'literal': 2})
        self.assertEqual(got['single_character_selections'], {'literal': 2})

    def test_lexer_context_and_ascii_guard(self):
        text = 'function f(x){return /a+/.test(x)?"x":12;}'
        p = subprocess.run(['node', str(a.HERE / 'lexical.cjs')], input=json.dumps({'x': text}),
                           text=True, capture_output=True, check=True)
        labels = json.loads(p.stdout)['x']
        self.assertEqual(labels[text.index('/a+/'):text.index('/a+/')+4], ['literal']*4)
        self.assertEqual(labels[text.index('test')], 'identifier')
        self.assertEqual(labels[text.index('?')], 'syntax.operator')
        self.assertEqual(labels[0], 'syntax.keyword')

    def test_allowlist_loader_does_not_open_other_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'allowed.js').write_text('ab')
            c = {'sources': [{'id': 1, 'relative_path': 'allowed.js', 'sha256': a.sha(b'ab')}]}
            self.assertEqual(a.load_sources(root, c), {1: 'ab'})


if __name__ == '__main__':
    unittest.main()
