import copy
import itertools
import random
import unittest

import mechanism
import proof


class ProofTests(unittest.TestCase):
    def test_tree_heap_boundaries_and_bans(self):
        rng=random.Random(42)
        for n in (1,2,4,9,33,65,129,256,257,260):
            texts={'x':'ab'*(n//2)+'a'*(n%2)}
            q={'x':[[rng.randrange(200) for _ in range(11)] for _ in range(n)]}
            ends={'x':[{j for j in range(i+1,n+1) if rng.randrange(17)==0} for i in range(n)]}
            self.assertEqual(mechanism.exact_caps(texts,q,100,ends,6),proof.tree_caps(texts,q,100,ends,6))

    def test_exact_assignment_certificates(self):
        rng=random.Random(43)
        for _ in range(80):
            counts=[rng.randrange(3) for _ in range(4)];n=sum(counts)
            costs=[[None if rng.randrange(4)==0 else rng.randrange(-9,10) for _ in counts] for _ in range(n)]
            values=[sum(costs[p][a] for p,a in enumerate(labels)) for labels in itertools.product(range(4),repeat=n)
                    if [labels.count(c) for c in range(4)]==counts and all(costs[p][a] is not None for p,a in enumerate(labels))]
            receipt=proof.assignment_proof(costs,counts)
            self.assertEqual(proof.verify_assignment(costs,counts,receipt),min(values) if values else None)

    def test_reject_corrupted_primal_dual_hall(self):
        costs=[[1,5],[4,2]];counts=[1,1];r=proof.assignment_proof(costs,counts)
        for field in ('value','row_potentials','category_potentials','assignment'):
            bad=copy.deepcopy(r)
            if field=='value':bad[field]+=1
            else:bad[field][0]+=1
            with self.assertRaises(AssertionError):proof.verify_assignment(costs,counts,bad)
        costs=[[None,1],[None,2]];r=proof.assignment_proof(costs,[1,1])
        self.assertFalse(r['feasible'])
        r['neighbors']+=1
        with self.assertRaises(AssertionError):proof.verify_assignment(costs,[1,1],r)
        with self.assertRaises(AssertionError):proof.infeasibility([[1,2],[3,4]],[1,1])


if __name__=='__main__':unittest.main()
