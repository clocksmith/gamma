"""Independent small-domain oracles for the added real development graphs."""
from collections import Counter
from itertools import combinations, product
import random
import unittest

from algsolve.synth import typed_codec, typed_development, typed_program, typed_recipes


def connected(n, edges):
    neighbors = [set() for _ in range(n)]
    for a, b in edges:
        neighbors[a].add(b)
        neighbors[b].add(a)
    seen, todo = {0}, [0]
    while todo:
        for b in neighbors[todo.pop()] - seen:
            seen.add(b)
            todo.append(b)
    return len(seen) == n


class CrossFamilyTargets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = typed_development.proposed()
        cls.graphs = {r['uid']: r['program'] for r in cls.rows}

    def run_graph(self, uid, *args):
        graph = self.graphs['lcd:' + str(uid)]
        return typed_program.execute(graph, dict(zip(graph['parameters'], args)),
                                     recipes=typed_recipes.catalog())

    def test_tree_against_exhaustive_connectivity(self):
        for n in range(1, 5):
            possible = list(combinations(range(n), 2))
            for mask in range(1 << len(possible)):
                edges = [list(e) for i, e in enumerate(possible) if mask & (1 << i)]
                self.assertEqual(self.run_graph(261, n, edges), len(edges) == n-1 and connected(n, edges))

    def test_timestamp_zero_disconnected_and_later_redundant_edges(self):
        rng = random.Random(20261017)
        for n in range(2, 8):
            possible = list(combinations(range(n), 2))
            for _ in range(20):
                edges = rng.sample(possible, rng.randrange(1, len(possible)+1))
                logs = [[t, *e] for t, e in enumerate(edges)]
                expected = next((t for t in range(len(logs)) if connected(n, edges[:t+1])), -1)
                rng.shuffle(logs)
                self.assertEqual(self.run_graph(1101, logs, n), expected)

    def test_unique_maximum_against_counter(self):
        for size in range(1, 6):
            for values in product(range(3), repeat=size):
                expected = max((x for x,c in Counter(values).items() if c == 1), default=-1)
                self.assertEqual(self.run_graph(1133, list(values)), expected)

    def test_capacity_against_subset_enumeration(self):
        rng = random.Random(20261017)
        for _ in range(60):
            weights = [rng.randrange(1,1001) for _ in range(rng.randrange(1,10))]
            expected = max(size for size in range(len(weights)+1)
                           if any(sum(xs) <= 5000 for xs in combinations(weights,size)))
            self.assertEqual(self.run_graph(1196, weights), expected)

    def test_meetings_against_pairwise_overlap(self):
        intervals = [[a,b] for a in range(4) for b in range(a+1,5)]
        graphs = [r['program'] for r in self.rows if r['uid'] == 'lcd:252']
        for size in range(4):
            for rows in combinations(intervals,size):
                expected = all(max(a[0],b[0]) >= min(a[1],b[1]) for a,b in combinations(rows,2))
                for graph in graphs:
                    self.assertEqual(typed_program.execute(graph, {'intervals':list(reversed(rows))}),expected)
        self.assertFalse(self.run_graph(252, [[0,1],[0,1]]))
        self.assertTrue(self.run_graph(252, [[999999,1000000]]))

    def test_critical_edges_against_all_spanning_trees(self):
        rng = random.Random(20261017)
        graphs = [r['program'] for r in self.rows if r['uid'] == 'lcd:1489']
        for n in range(2,7):
            for _ in range(12):
                endpoints = [(i,i+1) for i in range(n-1)]
                extra = [e for e in combinations(range(n),2) if e not in endpoints]
                endpoints += rng.sample(extra, min(len(extra),3))
                edges = [[a,b,rng.randrange(1,5)] for a,b in endpoints]
                rng.shuffle(edges)
                trees = [(sum(edges[i][2] for i in ids), set(ids))
                         for ids in combinations(range(len(edges)),n-1)
                         if connected(n,[edges[i][:2] for i in ids])]
                minimum = min(cost for cost,_ in trees)
                optimal = [ids for cost,ids in trees if cost == minimum]
                critical = set.intersection(*optimal)
                pseudo = set.union(*optimal)-critical
                for graph in graphs:
                    result = typed_program.execute(graph, {'n': n, 'edges': edges},
                                                   recipes=typed_recipes.catalog())
                    self.assertEqual(tuple(map(set,result)), (critical,pseudo))

    def test_maximum_edge_classification_with_critical_and_lighter_edges(self):
        # Complements the all-equal maximum-input proposal: forces the lighter
        # DSU writes and critical-edge branch without raising the frozen budget.
        edges = [[i,i+1,1] for i in range(99)] + [[0,99,1000]]
        edges += [[a,b,1000] for a in range(3) for b in range(a+2,99)][:100]
        for row in self.rows:
            if row['uid'] == 'lcd:1489':
                actual = typed_program.execute(row['program'], {'n':100,'edges':edges},
                    recipes=typed_recipes.catalog(),budget=typed_codec.EXECUTION_BUDGET)
                self.assertEqual(actual,(list(range(99)),[]))


if __name__ == '__main__':
    unittest.main()
