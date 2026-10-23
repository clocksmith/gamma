"""Invented strings only; explicit occurrences are confined to these tiny tests."""
import copy
import itertools
import random
import unittest
import implicit


def words(texts,banned):
    return sorted({text[i:j] for text in texts.values() for i in range(len(text)) for j in range(i+1,len(text)+1)}-set(banned))


def explicit(texts,banned,q,capacity,denominator):
    pool=words(texts,banned);weights={word:0 for word in pool};pathcost={}
    for pid,text in texts.items():
        d=[None]*len(text)+[0]
        for i in range(len(text)-1,-1,-1):
            choices=[]
            for j in range(i+1,len(text)+1):
                word=text[i:j]
                if word in weights:
                    penalty=q[pid][i][implicit.bin_index(j-i)];weights[word]+=penalty
                    if d[j] is not None:choices.append(d[j]+penalty+(9 if j-i==1 else -1)*denominator)
            if choices:d[i]=min(choices)
        if d[0] is None:raise ValueError('no full-pool path')
        pathcost[pid]=d[0]
    top=sum(sorted(weights.values(),reverse=True)[:capacity])
    return sum(pathcost.values())-top,top,pathcost,pool


def objective(texts,vocab):
    total=0;vocab=set(vocab)
    for text in texts.values():
        d=[None]*len(text)+[0]
        for i in range(len(text)-1,-1,-1):
            candidates=[d[j]+(9 if j-i==1 else -1) for j in range(i+1,len(text)+1) if text[i:j] in vocab and d[j] is not None]
            if candidates:d[i]=min(candidates)
        if d[0] is None:raise ValueError('dictionary cannot cover')
        total+=d[0]
    return total


class LengthSensitiveTests(unittest.TestCase):
    def test_random_exact_occurrence_expansion_and_gradient_counts(self):
        rng=random.Random(3501)
        for _ in range(160):
            texts={str(p):''.join(rng.choices('abc',k=rng.randrange(2,19))) for p in range(3)}
            possible=words(texts,set());banned=set(texts.values())|set(rng.sample(possible,min(4,len(possible))))
            q={p:[[rng.randrange(40) for _ in implicit.BINS] for _ in t] for p,t in texts.items()};cap=rng.randrange(0,20);den=11
            index=implicit.Index(texts,banned)
            try:expected,top,paths,pool=explicit(texts,banned,q,cap,den)
            except ValueError:
                with self.assertRaises(ValueError):index.certificate(q,cap,den)
                with self.assertRaises(ValueError):implicit.verify(index,q,cap,den)
                continue
            result=index.certificate(q,cap,den)
            self.assertEqual(result['numerator'],expected);self.assertEqual(result['top_capacity_numerator'],top)
            self.assertEqual(result['path_numerators'],paths);self.assertEqual(implicit.verify(index,q,cap,den),expected)
            all_selected=[(k,p['multiplicity']) for k,p in enumerate(index.pieces) if p['multiplicity']]
            self.assertEqual(sorted(index.selected_vocabulary(all_selected)),pool)
            chosen=index.selected_vocabulary(result['selected_pieces']);self.assertLessEqual(len(chosen),cap)
            self.assertEqual(len(chosen),len(set(chosen)))
            counts=index.selected_occurrences(result['selected_pieces'])
            for pid,text in texts.items():
                for i in range(len(text)):
                    actual=[sum(text.startswith(w,i) and implicit.bin_index(len(w))==b for w in chosen) for b in range(len(implicit.BINS))]
                    self.assertEqual(counts[pid][i],actual)

    def test_lifting_item33_is_exact_not_strict_improvement_claim(self):
        rng=random.Random(3502)
        for _ in range(60):
            texts={str(p):''.join(rng.choices('abcd',k=rng.randrange(2,30))) for p in range(2)}
            banned=set(texts.values());q={p:[rng.randrange(50) for _ in t] for p,t in texts.items()}
            old=implicit.parent.Index(texts,banned);new=implicit.Index(texts,banned);lift=implicit.lift_start_multipliers(q)
            for cap in (0,3,256):
                a=old.certificate(q,cap,17);b=new.certificate(lift,cap,17)
                self.assertEqual(a['numerator'],b['numerator']);self.assertEqual(a['top_capacity_numerator'],b['top_capacity_numerator'])
                self.assertEqual(implicit.verify(new,lift,cap,17),a['numerator'])

    def test_exhaustive_dictionary_weak_duality_and_rounding(self):
        rng=random.Random(3503)
        for _ in range(40):
            texts={'a':''.join(rng.choices('ab',k=4)),'b':''.join(rng.choices('ab',k=4))};banned=set(texts.values())
            index=implicit.Index(texts,banned);q={p:[[rng.randrange(30) for _ in implicit.BINS] for _ in t] for p,t in texts.items()}
            cert=index.certificate(q,3,7);pool=words(texts,banned);optimum=None
            for size in range(4):
                for selected in itertools.combinations(pool,size):
                    try:score=objective(texts,selected)
                    except ValueError:continue
                    optimum=score if optimum is None else min(optimum,score)
            if optimum is not None:self.assertLessEqual(cert['integer_lower_bound'],optimum)
            self.assertEqual(cert['integer_lower_bound'],-(-cert['numerator']//7))

    def test_supergradient_supports_concave_dual(self):
        rng=random.Random(3504);texts={'a':'abcabca','b':'bcababa'};index=implicit.Index(texts,set(texts.values()))
        for _ in range(40):
            q={p:[[rng.randrange(30) for _ in implicit.BINS] for _ in t] for p,t in texts.items()}
            other={p:[[rng.randrange(30) for _ in implicit.BINS] for _ in t] for p,t in texts.items()}
            cert=index.certificate(q,3,10);counts=index.selected_occurrences(cert['selected_pieces'])
            dot=sum((cert['path_starts'][p][i][b]-counts[p][i][b])*(other[p][i][b]-q[p][i][b])
                    for p,t in texts.items() for i in range(len(t)) for b in range(len(implicit.BINS)))
            self.assertLessEqual(index.certificate(other,3,10)['numerator'],cert['numerator']+dot)

    def test_all_bin_boundaries_exact_bans_and_unbounded_last_bin(self):
        text=''.join(chr(1000+i) for i in range(270));texts={'a':text}
        lengths=[1,2,3,4,5,8,9,16,17,32,33,64,65,128,129,256,257,269,270]
        banned={text[:n] for n in lengths}|{text[7:7+n] for n in lengths if 7+n<=len(text)}
        index=implicit.Index(texts,banned);q={'a':[[((i+3)*(b+7))%53 for b in range(len(implicit.BINS))] for i in range(len(text))]}
        expected,top,paths,pool=explicit(texts,banned,q,256,10)
        actual=index.certificate(q,256,10)
        self.assertEqual(actual['numerator'],expected);self.assertEqual(implicit.verify(index,q,256,10),expected)
        self.assertEqual(index.distinct_allowed_entries,len(pool));self.assertEqual(actual['path_numerators'],paths)
        self.assertTrue(any(p['bin']==10 and p['multiplicity'] for p in index.pieces))

    def test_dominated_endpoint_survives_a_banned_minimum(self):
        # Bin5-8 at start0 must retain end6 despite end5 having lower distance.
        # This is why a monotone deque that discards dominated entries is unsafe.
        tree=implicit.MinimumTree(10);tree.set(5,(-10,5));tree.set(6,(1,6));tree.set(7,(3,7))
        self.assertEqual(implicit.interval_minimum(tree,5,8,[5]),(1,6))
        texts={'a':'abcdefghijklmno'};banned={'abcde','abcdefg','abcdefgh','abcdefghijklmno'}
        q={'a':[[7*i+3*b for b in range(len(implicit.BINS))] for i in range(15)]}
        expected=explicit(texts,banned,q,4,9)[0];index=implicit.Index(texts,banned)
        self.assertEqual(index.certificate(q,4,9)['numerator'],expected)
        self.assertEqual(implicit.verify(index,q,4,9),expected)

    def test_no_quadratic_word_inventory_and_large_integers(self):
        text=''.join(chr(2000+i) for i in range(700));index=implicit.Index({'a':text},{text})
        self.assertEqual(index.distinct_allowed_entries,700*701//2-1)
        self.assertLessEqual(len(index.pieces),len(implicit.BINS)*len(index.base.groups))
        q={'a':[[10**50+i+3*b for b in range(len(implicit.BINS))] for i in range(700)]}
        self.assertEqual(index.certificate(q,256,10**30)['numerator'],implicit.verify(index,q,256,10**30))

    def test_corrupt_splits_bans_suffix_membership_and_invalid_q_rejected(self):
        texts={'a':'abcabc','b':'abcb'};banned=set(texts.values())|{'ab'}
        def fresh():return implicit.Index(texts,banned)
        q={p:[[2]*len(implicit.BINS) for _ in t] for p,t in texts.items()}
        index=fresh();index.pieces[0]['multiplicity']+=1
        with self.assertRaises(AssertionError):implicit.verify(index,q,3,10)
        index=fresh();index.pieces.pop()
        with self.assertRaises(AssertionError):implicit.verify(index,q,3,10)
        index=fresh();index.pieces[0]['bin']+=1
        with self.assertRaises(AssertionError):implicit.verify(index,q,3,10)
        index=fresh();index.base.banned_ends['a'][0].clear()
        with self.assertRaises(AssertionError):implicit.verify(index,q,3,10)
        index=fresh();index.base.positions.reverse()
        with self.assertRaises(AssertionError):implicit.verify(index,q,3,10)
        index=fresh();bad=copy.deepcopy(q);bad['a'][0][0]=-1
        with self.assertRaises(AssertionError):index.certificate(bad,3,10)
        bad=copy.deepcopy(q);bad['a'][0][0]=True
        with self.assertRaises(AssertionError):implicit.verify(index,bad,3,10)
        with self.assertRaises(AssertionError):index.certificate(q,3,0)

    def test_unencodable_pool_and_shortest_longest_witness_variants(self):
        index=implicit.Index({'a':'a'},{'a'});q={'a':[[0]*len(implicit.BINS)]}
        with self.assertRaises(ValueError):index.certificate(q,256,1)
        with self.assertRaises(ValueError):implicit.verify(index,q,256,1)
        index=implicit.Index({'a':'abcdefghijklmnop'},{'abcdefghijklmnop'});q={'a':[[i+1]*len(implicit.BINS) for i in range(16)]}
        result=index.certificate(q,5,1)
        short=index.selected_vocabulary(result['selected_pieces']);long=index.selected_vocabulary(result['selected_pieces'],True)
        self.assertEqual(len(short),len(long));self.assertEqual(len(short),5)
        self.assertEqual(sum(len(s) for s in long)>=sum(len(s) for s in short),True)
        self.assertFalse(set(short)&index.base.banned);self.assertFalse(set(long)&index.base.banned)

if __name__=='__main__':unittest.main()
