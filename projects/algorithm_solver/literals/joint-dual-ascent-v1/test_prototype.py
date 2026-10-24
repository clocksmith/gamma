"""Exhaustive invented paths/dictionaries; no private inputs or production runs."""
from itertools import combinations,product
import unittest
import prototype as p


def all_paths(text,banned,start=0):
    if start==len(text):return [()]
    return [((start,end,p.dual.bin_index(end-start)),)+tail for end in range(start+1,len(text)+1)
            if text[start:end] not in banned for tail in all_paths(text,banned,end)]


def path_cost(edges,q,D):return sum(D*(9 if b==0 else -1)+q[start][b] for start,end,b in edges)


def pool(texts,banned):
    return sorted({text[start:end] for text in texts.values() for start in range(len(text)) for end in range(start+1,len(text)+1)}-banned)


def brute(index,q,capacity,D,median,p95):
    ids=sorted(index.texts);choices=[all_paths(index.texts[pid],index.base.banned) for pid in ids]
    best=None
    for paths in product(*choices):
        lengths=sorted(map(len,paths));n=len(lengths)
        if lengths[n//2-1]+lengths[n//2]>2*median or lengths[(95*n+99)//100-1]>p95:continue
        cost=sum(path_cost(path,q[pid],D) for pid,path in zip(ids,paths))
        best=cost if best is None else min(best,cost)
    words=pool(index.texts,index.base.banned);weights={}
    for word in words:
        b=p.dual.bin_index(len(word));weights[word]=sum(q[pid][start][b] for pid,text in index.texts.items() for start in range(len(text)) if text.startswith(word,start))
    top=max(sum(weights[w] for w in subset) for k in range(min(capacity,len(words))+1) for subset in combinations(words,k))
    return None if best is None else best-top


class PrototypeTests(unittest.TestCase):
    def test_exhaustive_joint_objective_supergradient_and_concavity(self):
        texts={str(i):text for i,text in enumerate(('aabb','abba','baab','bbaa'))}
        banned=set(texts.values())|{'aab'};index=p.dual.Index(texts,banned);D=3;points=[]
        for a,b in product(range(3),repeat=2):
            q=p.zeros(texts);q['0'][0][1]=a;q['1'][2][1]=b
            got=p.oracle(index,q,2,D,median_cap=2,p95_cap=3)
            self.assertTrue(got['joint_family_feasible']);self.assertEqual(got['numerator'],brute(index,q,2,D,2,3))
            for pid,path in got['paths'].items():
                self.assertEqual(''.join(texts[pid][start:end] for start,end,binno in path),texts[pid])
                self.assertTrue(all(texts[pid][start:end] not in banned for start,end,binno in path))
            points.append((q,got))
        # Every ordered pair in a 3x3 multiplier grid, not sampled inequalities.
        for q,got in points:
            for other,target in points:
                delta={pid:[[y-x for x,y in zip(row,second)] for row,second in zip(q[pid],other[pid])] for pid in q}
                self.assertLessEqual(target['numerator'],got['numerator']+p.dot(got['gradient'],delta))
                # B(q+r;2D)=2 B((q+r)/2;D), checked with integer arithmetic.
                summed={pid:[[x+y for x,y in zip(row,second)] for row,second in zip(q[pid],other[pid])] for pid in q}
                midpoint=p.oracle(index,summed,2,2*D,median_cap=2,p95_cap=3)
                self.assertGreaterEqual(midpoint['numerator'],got['numerator']+target['numerator'])

    def test_dictionary_multiplicity_tie_and_global_exact_bans(self):
        texts={'0':'abcdefghij','1':'klmnopqrst'};banned=set(texts.values())|{'abcdef'}
        index=p.dual.Index(texts,banned);q=p.zeros(texts);q['0'][0][4]=5
        top,selected=index.weighted_selection(q,3);counts=index.selected_occurrences(selected)
        self.assertEqual(top,15);self.assertEqual(counts['0'][0][4],3)
        self.assertEqual(index.selected_vocabulary(selected),['abcde','abcdefg','abcdefgh'])
        self.assertEqual(p.dot(q,counts),top)
        self.assertEqual(sum(count for piece,count in selected),3)
        self.assertTrue(any(count>1 for piece,count in selected))
        words=index.selected_vocabulary(selected)
        for pid,text in texts.items():
            for start,row in enumerate(counts[pid]):
                for b,value in enumerate(row):
                    self.assertEqual(value,sum(text.startswith(word,start) and p.dual.bin_index(len(word))==b for word in words))

    def test_exact_negative_dag_recovery_and_explicit_endpoint_cap(self):
        text='abcdefghi';banned={text,'abcd'};index=p.dual.Index({'0':text},banned);q=p.zeros({'0':text})['0'];D=7
        for k in (None,2,3,4,5):
            edges,value,nbytes=p.recover(text,q,index.base.banned_ends['0'],D,k)
            paths=[x for x in all_paths(text,banned) if k is None or len(x)==k]
            target=min(paths,key=lambda path:(path_cost(path,q,D),tuple(end for start,end,b in path)))
            self.assertEqual(value,path_cost(target,q,D));self.assertEqual(tuple(edges),target)
            self.assertEqual(nbytes,4*(len(text)+1)*(k or 1))
        with self.assertRaises(MemoryError):p.recover(text,q,index.base.banned_ends['0'],D,4,endpoint_bytes=159)

    def test_integer_projection_retains_zero_best_and_no_upper_bound(self):
        q={'0':[[0,4,8]]};g={'0':[[1,-2,-10]]}
        self.assertEqual(p.update(q,g,3),{'0':[[3,0,0]]})
        with self.assertRaises(AssertionError):p.update(q,g,.5)
        best=(-10,'zero')
        for value,label in ((-12,'worse'),(-10,'tie'),(-8,'better')):
            if value>best[0]:best=(value,label)
        self.assertEqual(best,(-8,'better'))


if __name__=='__main__':unittest.main()
