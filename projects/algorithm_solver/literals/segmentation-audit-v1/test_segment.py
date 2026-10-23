import itertools
import random
import unittest
from segment import encode


def paths(text,vocab):
    if not text:return [()]
    return [(i,)+seq for i,word in enumerate(vocab) if text.startswith(word) for seq in paths(text[len(word):],vocab)]

def key(seq,vocab,policy):
    chars=sum(len(vocab[i])==1 for i in seq)
    primary=(len(seq),0) if policy=='canonical' else (len(seq),chars) if policy=='shortest_min_char' else (len(seq),-chars) if policy=='shortest_max_char' else (chars,len(seq))
    return primary,seq

class SegmentTests(unittest.TestCase):
    def test_exhaustive_tiny_paths(self):
        rng=random.Random(16)
        for _ in range(150):
            text=''.join(rng.choice('ab') for _ in range(rng.randint(0,7)))
            extras=rng.sample(['aa','ab','ba','bb','aaa','aab','aba','abb','baa','bab','bba','bbb'],rng.randint(0,6))
            vocab=['a','b']+extras;allpaths=paths(text,vocab)
            for policy in ('canonical','shortest_min_char','shortest_max_char','min_char'):
                actual=tuple(encode(text,vocab,policy));self.assertEqual(actual,min(allpaths,key=lambda seq:key(seq,vocab,policy)))
    def test_equal_selection_different_character_count(self):
        vocab=['a','b','c','d','abc','ab','cd'];text='abcd'
        self.assertEqual(encode(text,vocab,'canonical'),[4,3])
        self.assertEqual(encode(text,vocab,'shortest_min_char'),[5,6])
        self.assertEqual(encode(text,vocab,'shortest_max_char'),[4,3])
    def test_character_objective_can_cost_extra_selections(self):
        vocab=list('abcdefg')+['abcdef','ab','cd','efg'];text='abcdefg'
        self.assertEqual(len(encode(text,vocab,'shortest_min_char')),2)
        self.assertEqual(encode(text,vocab,'min_char'),[8,9,10])
    def test_unencodable_rejected(self):
        with self.assertRaises(ValueError):encode('z',['a'],'min_char')

if __name__=='__main__':unittest.main()
