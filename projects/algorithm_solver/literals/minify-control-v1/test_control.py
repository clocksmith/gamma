"""Focused checks for control.py: spans-only proposals, exact cross-applied parsing, decomposition."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import control
audit = control.module('joint_v1_audit', control.LIT / 'joint-v1/audit.py')

SOURCES = {1: {'original': 'function solve(a){let r=0;for(let x of a){r+=x;}return r;}'},
           2: {'original': 'function solve(a){let r=1;for(let x of a){r*=x;}return r;}'},
           3: {'original': 'function solve(a,b){let r=0;for(let x of a){r+=x*b;}return r;}'}}


class Control(unittest.TestCase):
    def test_spans_only_proposer_never_returns_designed_forms(self):
        state = control.joint.evaluate(SOURCES, list(control.ALPHABET), 8)
        designed = ['ZZZ never in a source', 'for(let x of a){']
        spans = control.m2.hybrid_chosen([], SOURCES)(SOURCES, state, 40, 0.25)
        mined = control.m2.proposals_chosen(SOURCES, state, 10 ** 9)[:40]
        self.assertEqual(spans, mined)
        hybrid = control.m2.hybrid_chosen(designed, SOURCES)(SOURCES, state, 40, 0.25)
        self.assertNotIn('ZZZ never in a source', spans + hybrid)  # unwitnessed designed forms never enter

    def test_cross_applied_dictionary_parses_exactly(self):
        vocab = list(control.ALPHABET) + ['function solve(a', 'for(let x of a){r', 'return r;}', 'let r=']
        other = {pid: {'minified': v['original'].replace('let ', 'var ')} for pid, v in SOURCES.items()}
        for pool in (SOURCES, other):
            st = control.joint.evaluate(pool, vocab, 8)
            for pid, v in st['chosen'].items():
                parts = st['parsed'][pid, v]
                self.assertEqual(''.join(parts), pool[pid][v])
                self.assertEqual(len(parts), audit.minimum_count(pool[pid][v], vocab))

    def test_decomposition_adds_up_both_ways(self):
        sel = {('D_O', 'O'): 100, ('D_O', 'R'): 70, ('D_R', 'O'): 120, ('D_R', 'R'): 50}
        d = control.decompose(sel, 'O', 'R')
        self.assertEqual(d['total'], -50)
        self.assertEqual(d['via_D_x']['source'] + d['via_D_x']['adaptation'], d['total'])
        self.assertEqual(d['via_D_y']['source'] + d['via_D_y']['adaptation'], d['total'])
        self.assertEqual(d['via_D_x'], {'source': -30, 'adaptation': -20})


if __name__ == '__main__':
    unittest.main()
