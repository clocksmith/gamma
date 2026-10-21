import unittest
from search import ALPHABET, exact_addition, sequences, proposals

class MarginalTests(unittest.TestCase):
    def test_overlapping_occurrences_are_not_counted_twice(self):
        texts={'a':'aaaaa','b':'aaaa'}; vocab=list(ALPHABET)
        current=sequences(texts,vocab)
        gain, final=exact_addition(texts,vocab,current,'aaa')
        self.assertEqual(gain,4)  # Not the six overlapping matches times two.
        self.assertEqual([len(final[k]) for k in texts],[3,2])

    def test_existing_fragments_can_make_frequent_substrings_useless(self):
        texts={'a':'abcdabcd','b':'abcdabcd'};vocab=list(ALPHABET)+['abcd']
        current=sequences(texts,vocab)
        self.assertEqual(exact_addition(texts,vocab,current,'abc')[0],0)
        self.assertEqual(exact_addition(texts,vocab,current,'abcdabcd')[0],2)

    def test_proposals_exclude_whole_answers_and_one_problem_fragments(self):
        texts={'a':'unique abcd','b':'abcd repeat'};vocab=list(ALPHABET)
        candidates=proposals(texts,vocab,sequences(texts,vocab))
        self.assertIn('abcd',candidates)
        self.assertNotIn('uniq',candidates)
        self.assertFalse(set(candidates)&set(texts.values()))

    def test_new_ascii_character_uses_counted_base_entry(self):
        self.assertEqual(len(ALPHABET),96)
        self.assertEqual(len(sequences({'a':'@'},ALPHABET)['a']),1)

if __name__=='__main__':unittest.main()
