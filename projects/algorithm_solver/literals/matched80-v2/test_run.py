"""Focused checks for iteration 2's candidate sources; synthetic, no corpus search."""
import unittest

import run

TEXTS = {'1': 'abcabc\nxyz\n', '2': 'abc xyz\nabc\n', '3': 'xyz\nxyzabc\n'}
DESIGNED = ['abc', 'xyz\n', 'never-present']


class Candidates(unittest.TestCase):
    def setUp(self):
        self.vocab = list(run.base.ALPHABET)
        self.current = run.base.sequences(TEXTS, self.vocab)

    def test_span_ranking_is_unchanged_scale_v2_order(self):
        self.assertEqual(run.candidates('span', DESIGNED, 12)(TEXTS, self.vocab, self.current, set()),
                         run.base.proposals(TEXTS, self.vocab, self.current))

    def test_hybrid_reserves_a_quarter_of_the_shortlist_for_designed_pieces(self):
        mined = run.base.proposals(TEXTS, self.vocab, self.current)
        late = [s for s in mined[6:] if s not in mined[:6]][:2]  # designed pieces mining ranks low
        shortlist = run.candidates('hybrid', late + ['never-present'], 8)(TEXTS, self.vocab, self.current, set())[:8]
        self.assertEqual(shortlist[:6], mined[:6])
        self.assertEqual(sorted(shortlist[6:]), sorted(late))
        self.assertNotIn('never-present', shortlist)

    def test_hybrid_never_repeats_a_candidate(self):
        listed = run.candidates('hybrid', DESIGNED, 8)(TEXTS, self.vocab, self.current, set())
        self.assertEqual(len(listed), len(set(listed)))


if __name__ == '__main__':
    unittest.main()
