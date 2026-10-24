"""Small invented sources only; explicit pools belong solely to these tests."""
import copy
import itertools
import random
import unittest
import prototype as p
import public_audit


def words(texts, banned):
    return sorted({t[i:j] for t in texts.values() for i in range(len(t))
                   for j in range(i+1, len(t)+1)} - set(banned))


def path_cost(texts, vocab, q=None, denominator=1):
    result = 0
    for pid, t in texts.items():
        d = [None]*len(t)+[0]
        for i in range(len(t)-1, -1, -1):
            choices = [d[j]+denominator*(9 if j-i == 1 else -1)
                       +(q[pid][i][p.parent.bin_index(j-i)] if q else 0)
                       for j in range(i+1, len(t)+1)
                       if t[i:j] in vocab and d[j] is not None]
            if choices: d[i] = min(choices)
        if d[0] is None: return None
        result += d[0]
    return result


class ProofTests(unittest.TestCase):
    def test_explicit_dictionary_activation_and_weak_duality(self):
        rng = random.Random(4901)
        for _ in range(18):
            texts = {str(i): ''.join(rng.choices('ab', k=4)) for i in range(2)}
            banned = set(texts.values()); pool = words(texts, banned)
            index = p.parent.Index(texts, banned)
            q = {pid: [[rng.randrange(9) for _ in p.parent.BINS] for c in t] for pid,t in texts.items()}
            weights = {w: sum(q[pid][i][p.parent.bin_index(len(w))]
                             for pid,t in texts.items() for i in range(len(t))
                             if t.startswith(w,i)) for w in pool}
            support = {w: sum(w in t for t in texts.values()) for w in pool}
            cert = p.certificate(index,q,3,7,(0,1,2,3))
            for row in cert['rows']:
                feasible = [v for n in range(4) for v in itertools.combinations(pool,n)
                            if sum(support[w] == 1 for w in v) <= row['k']]
                self.assertEqual(row['weight'], max(sum(weights[w] for w in v) for v in feasible))
                self.assertEqual(row['numerator'], path_cost(texts,set(pool),q,7)-row['weight'])
                for v in feasible:
                    f = path_cost(texts,set(v))
                    if f is not None: self.assertLessEqual(row['integer_lower_bound'],f)
            self.assertEqual(cert['rows'][-1]['numerator'],index.certificate(q,3,7)['numerator'])

    def test_owner_intervals_singletons_and_bans(self):
        texts = {'a':'ababx','b':'ababy','c':'ababx'}; banned={'abab','ababx','ababy'}
        index=p.parent.Index(texts,banned); classes=p.support_classes(index)
        pool=words(texts,banned); seen=[]
        for i,piece in enumerate(index.pieces):
            pid,start=index.base.positions[piece['lo']]
            for n in range(piece['first'],piece['last']+1):
                if n in piece['excluded_lengths']: continue
                w=texts[pid][start:start+n]; seen.append(w)
                self.assertEqual(classes[i],1 if sum(w in t for t in texts.values())==1 else 2)
        self.assertEqual(sorted(seen),pool)
        self.assertEqual(sum('y' in t for t in texts.values()),1)
        self.assertEqual(sum('x' in t for t in texts.values()),2)

    def test_fewer_entries_zero_empty_classes_ties_and_multiplicity(self):
        for records in ([],[(0,10**9,0)],[(8,10**9,0),(9,1,1),(8,1,2)],[(3,1,0)]):
            actual=p.top_slots(records,4)
            expanded=sorted((w for w,n,i in records for _ in range(min(n,4))),reverse=True)[:4]
            self.assertEqual(actual,[0]+[sum(expanded[:j]) for j in range(1,len(expanded)+1)])
        self.assertEqual(p.capacity_term([0],[0],256,0)['weight'],0)
        self.assertEqual(p.capacity_term([0,7],[0,3],256,256)['weight'],10)
        self.assertEqual(p.capacity_term([0,0],[0,0],1,1)['one_owner_slots'],0)

    def test_bin_boundaries_and_zero_q(self):
        texts={'a': ''.join(chr(1000+i) for i in range(270))}; banned={texts['a']}
        index=p.parent.Index(texts,banned)
        q={'a':[[0]*len(p.parent.BINS) for _ in texts['a']]}
        cert=p.certificate(index,q)
        self.assertTrue(all(x==1 for x in p.support_classes(index)))
        self.assertEqual(len({r['numerator'] for r in cert['rows']}),1)
        self.assertEqual(cert['rows'][-1]['numerator'],index.certificate(q)['numerator'])

    def test_public_theorem_reconciliation_and_corruption(self):
        arm={'cohort':'R','complete':True,'fit_problems':300,'capacity':256,
             'source_bans_pool_q_and_packets_replayed':True,'initial_q_all_zero':True,
             'initial_numerator':-900,'certificate':{
                 'independent_partition_and_integer_replay':True,'denominator':10,
                 'numerator':-600,'top_capacity_numerator':300,
                 'path_numerators':{str(i):-1 for i in range(300)},'integer_lower_bound':-60}}
        other=copy.deepcopy(arm);other['cohort']='naming'
        data={'complete':True,'arms':[arm,other]}
        self.assertEqual(public_audit.audit(data)['rows'][0]['two_point_bound_ceiling_for_every_k'],-30)
        bad=copy.deepcopy(data);bad['arms'][0]['certificate']['top_capacity_numerator']+=1
        with self.assertRaises(AssertionError):public_audit.audit(bad)


if __name__=='__main__': unittest.main()
