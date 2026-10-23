"""Generic-only exhaustive checks; never opens any research corpus."""
import itertools
import random
import sys
import unittest
from pathlib import Path
import implicit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'fraction-capacity-v1'))
import dual


def words(texts,banned):
    return sorted({text[i:j] for text in texts.values() for i in range(len(text))
                   for j in range(i+1,len(text)+1)}-set(banned))


class ImplicitTests(unittest.TestCase):
    def test_random_full_pool_certificate_equals_explicit_occurrence_dual(self):
        rng=random.Random(330)
        for _ in range(180):
            texts={str(i):''.join(rng.choices('abc',k=rng.randrange(2,10))) for i in range(3)}
            possible=words(texts,set());banned=set(texts.values())|set(rng.sample(possible,min(3,len(possible))))
            pool=words(texts,banned);index=implicit.Index(texts,banned)
            self.assertEqual(index.distinct_allowed_entries,len(pool))
            all_selected=[(i,g['multiplicity']) for i,g in enumerate(index.groups) if g['multiplicity']]
            self.assertEqual(sorted(index.selected_vocabulary(all_selected)),pool)
            q={pid:[rng.randrange(50) for _ in text] for pid,text in texts.items()};cap=rng.randrange(1,12);den=10
            graph=dual.Graph(texts,pool,[])
            expanded=[q[pid][start] for pid,start,end,entry in graph.order]
            try:
                expected=dual.independent_certificate(texts,pool,[],expanded,cap,den)
            except AssertionError:
                with self.assertRaises(ValueError):index.certificate(q,cap,den)
                with self.assertRaises(ValueError):implicit.verify(index,q,cap,den)
                continue
            actual=index.certificate(q,cap,den)
            self.assertEqual(actual['numerator'],expected)
            self.assertEqual(implicit.verify(index,q,cap,den),expected)
            selected=index.selected_vocabulary(actual['selected_groups'])
            self.assertLessEqual(len(selected),cap)
            explicit_sum=sum(sum(q[pid][i] for pid,text in texts.items() for i in range(len(text)) if text.startswith(word,i)) for word in selected)
            self.assertEqual(actual['top_capacity_numerator'],explicit_sum)
            counts=index.selected_occurrences(actual['selected_groups'])
            for pid,text in texts.items():
                self.assertEqual(counts[pid],[sum(text.startswith(word,i) for word in selected) for i in range(len(text))])

    def test_exhaustive_feasible_dictionary_weak_duality(self):
        rng=random.Random(331)
        for _ in range(40):
            texts={'a':''.join(rng.choices('ab',k=4)),'b':''.join(rng.choices('ab',k=4))}
            banned=set(texts.values());pool=words(texts,banned);index=implicit.Index(texts,banned);capacity=3
            q={pid:[rng.randrange(20) for _ in text] for pid,text in texts.items()};cert=index.certificate(q,capacity,10)
            opt=None
            for count in range(capacity+1):
                for subset in itertools.combinations(pool,count):
                    try:value=dual.objective(texts,list(subset))
                    except ValueError:continue
                    opt=value if opt is None else min(opt,value)
            if opt is not None:self.assertLessEqual(cert['integer_lower_bound'],opt)

    def test_whole_source_bans_repetition_prefixes_and_one_owner(self):
        texts={'a':'aaaaaa','b':'aaa','c':'xyzxyz','d':'xyz'};banned={'aaaaaa','aaa','xyzxyz','xyz','aa','y'}
        index=implicit.Index(texts,banned);pool=words(texts,banned)
        self.assertEqual(index.distinct_allowed_entries,len(pool))
        self.assertIn('aaaaa',pool) # one-owner near-whole entry remains in the relaxation
        q={pid:[10**40+i for i in range(len(text))] for pid,text in texts.items()}
        self.assertEqual(index.certificate(q,5,10**20)['numerator'],implicit.verify(index,q,5,10**20))

    def test_positive_bound_and_zero_character_witness(self):
        index=implicit.Index({'a':'ab'},{'ab'});q={'a':[0,0]}
        self.assertEqual(index.certificate(q,2,1)['integer_lower_bound'],18)
        self.assertEqual(implicit.verify(index,q,2,1),18)
        self.assertEqual(dual.objective({'a':'aaaa'},['aa']),-2)

    def test_quadratic_space_is_implicit(self):
        # Distinct Unicode characters produce n(n+1)/2 strings but n groups.
        text=''.join(chr(1000+i) for i in range(700));index=implicit.Index({'a':text},{text})
        self.assertEqual(index.distinct_allowed_entries,700*701//2-1)
        self.assertEqual(len(index.groups),700)
        q={'a':[i%17 for i in range(700)]}
        self.assertEqual(index.certificate(q,256,100)['numerator'],implicit.verify(index,q,256,100))

    def test_verifier_rejects_missing_group_and_wrong_membership(self):
        texts={'a':'abcabc','b':'abxy'};index=implicit.Index(texts,set(texts.values()));q={pid:[1]*len(text) for pid,text in texts.items()}
        removed=index.groups.pop()
        with self.assertRaises(AssertionError):implicit.verify(index,q,3,10)
        index.groups.append(removed);index.groups.sort(key=lambda g:(g['lo'],g['hi'],g['first']))
        index.groups[0]['last']+=1
        with self.assertRaises(AssertionError):implicit.verify(index,q,3,10)
        index=implicit.Index(texts,set(texts.values()))
        index.distinct_allowed_entries+=1
        with self.assertRaises(AssertionError):implicit.verify(index,q,3,10)

    def test_independent_suffix_validation_repetition_and_corruption(self):
        texts={'a':'a'*1200+'b','b':'a'*1200+'b','c':'a'*900}
        index=implicit.Index(texts,set(texts.values()))
        q={pid:[i%13 for i in range(len(text))] for pid,text in texts.items()}
        self.assertEqual(index.certificate(q,256,100)['numerator'],implicit.verify(index,q,256,100))
        index.lcp[-1]+=1
        with self.assertRaises(AssertionError):implicit.verify(index,q,256,100)
        index=implicit.Index({'a':'abc','b':'bca'},{'abc','bca'})
        q={'a':[1,1,1],'b':[1,1,1]}
        index.positions[0],index.positions[-1]=index.positions[-1],index.positions[0]
        with self.assertRaises(AssertionError):implicit.verify(index,q,3,10)


if __name__=='__main__':unittest.main()
