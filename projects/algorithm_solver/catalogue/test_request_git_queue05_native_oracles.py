"""Stdlib controls for semantic traces only; no native candidates."""
from collections import Counter
from copy import deepcopy
from itertools import product
import heapq
import unittest
from . import imported_qualification as q
from . import request_git_queue05_native_oracles as o


def trace(pid, init, steps):
    return [[o.CLASSES[pid]]+[op for op, _ in steps], [init]+[a for _, a in steps]]


class NativeSemanticTests(unittest.TestCase):
    def test_allocator_allocation_and_free(self):
        args = trace(2502, [5], [('allocate', [1, 7]), ('allocate', [2, 8]), ('allocate', [1, 7]), ('freeMemory', [7]), ('allocate', [2, 9]), ('freeMemory', [8]), ('allocate', [2, 9])])
        self.assertEqual(o.expected(2502, args), [None, 0, 1, 3, 2, 3, 2, 0])

    def test_allocator_occupied_set_model(self):
        actions = [('allocate', [1, 1]), ('allocate', [2, 2]), ('freeMemory', [1]), ('freeMemory', [2])]
        for steps in product(actions, repeat=4):
            blocks = {}; answer = [None]
            for op, a in steps:
                if op == 'freeMemory':
                    answer.append(len(blocks.pop(a[0], set())))
                else:
                    occupied = set().union(*blocks.values()); size, identity = a
                    start = next((i for i in range(5-size+1) if set(range(i, i+size)).isdisjoint(occupied)), -1)
                    if start >= 0:
                        blocks.setdefault(identity, set()).update(range(start, start+size))
                    answer.append(start)
            self.assertEqual(o.expected(2502, trace(2502, [5], list(steps))), answer)

    def test_stream_run_length(self):
        for k in range(1, 6):
            for seq in product((1, 2), repeat=7):
                run = 0; answer = [None]
                for value in seq:
                    run = run+1 if value == 1 else 0; answer.append(run >= k)
                self.assertEqual(o.expected(2526, trace(2526, [1, k], [('consec', [v]) for v in seq])), answer)

    def test_graph_independent_dijkstra(self):
        pairs = [(i, j) for i in range(3) for j in range(3) if i != j]
        for weights in product((0, 2), repeat=6):
            edges = [[i, j, w] for (i, j), w in zip(pairs, weights) if w]; answer = [None]
            for start in range(3):
                distances = [10**20]*3; distances[start] = 0; heap = [(0, start)]
                while heap:
                    distance, u = heapq.heappop(heap)
                    if distance != distances[u]:
                        continue
                    for v, w in [(v, w) for x, v, w in edges if x == u]:
                        if distance+w < distances[v]:
                            distances[v] = distance+w; heapq.heappush(heap, (distance+w, v))
                answer.extend(-1 if x == 10**20 else x for x in distances)
            args = trace(2642, [3, edges], [('shortestPath', [i, j]) for i in range(3) for j in range(3)])
            self.assertEqual(o.expected(2642, args), answer)

    def test_graph_updates_directed_reachable(self):
        args = trace(2642, [3, [[0, 1, 8]]], [('shortestPath', [1, 0]), ('shortestPath', [0, 2]), ('addEdge', [[1, 2, 2]]), ('shortestPath', [0, 2]), ('addEdge', [[0, 2, 1]]), ('shortestPath', [0, 2])])
        self.assertEqual(o.expected(2642, args), [None, -1, -1, None, 10, None, 1])

    def test_frequency_counter(self):
        actions = [('add', [1]), ('add', [2]), ('deleteOne', [1]), ('hasFrequency', [1]), ('hasFrequency', [2])]
        for steps in product(actions, repeat=4):
            counts = Counter(); answer = [None]
            for op, a in steps:
                result = None
                if op == 'add':
                    counts[a[0]] += 1
                elif op == 'deleteOne':
                    counts[a[0]] = max(0, counts[a[0]]-1)
                else:
                    result = a[0] in counts.values()
                answer.append(result)
            self.assertEqual(o.expected(2671, trace(2671, [], list(steps))), answer)

    def test_input_preservation_and_empty_instances(self):
        for pid, init in [(2502, [4]), (2526, [9, 2]), (2642, [3, [[0, 2, 7]]]), (2671, [])]:
            args = trace(pid, init, []); before = deepcopy(args)
            self.assertEqual(o.expected(pid, args), [None]); self.assertEqual(args, before)
        args = trace(2642, [3, [[0, 2, 7]]], [('addEdge', [[2, 1, 4]]), ('shortestPath', [0, 1])]); before = deepcopy(args)
        self.assertEqual(o.expected(2642, args), [None, None, 11]); self.assertEqual(args, before)

    def test_full_domain_separate_reference_budget(self):
        examples = [(2502, trace(2502, [1000], [('allocate', [1000, 1000])]*1000)),
                    (2526, trace(2526, [10**9, 100000], [('consec', [10**9])]*100000)),
                    (2642, trace(2642, [100, [[i, j, 10**6] for i in range(100) for j in range(100) if i != j]], [('shortestPath', [0, 99])]*100)),
                    (2671, trace(2671, [], [('add', [1])]*200000))]
        for pid, args in examples:
            o.validate(pid, args)
            with self.assertRaises(ValueError):
                o.expected(pid, args)
        for pid in (2526, 2671):
            args = dict(examples)[pid]
            self.assertGreater(len(q.encoded(q.packet([{'args': args}]))), q.MAX_PACKET)

    def test_invalid_domains(self):
        bad = [(2502, trace(2502, [True], [])), (2502, trace(2502, [1], [('allocate', [0, 1])])),
               (2526, trace(2526, [1, 0], [])), (2526, trace(2526, [1, 1], [('consec', [10**9+1])])),
               (2642, trace(2642, [2, [[0, 0, 1]]], [])), (2642, trace(2642, [2, [[0, 1, 1], [0, 1, 2]]], [])),
               (2642, trace(2642, [2, [[0, 1, 1]]], [('addEdge', [[0, 1, 2]])])),
               (2642, trace(2642, [2, []], [('shortestPath', [0, 1])]*101)),
               (2671, trace(2671, [], [('hasFrequency', [0])])), (2671, trace(2671, [], [('add', [False])])),
               (2671, [['FrequencyTracker', 'FrequencyTracker'], [[], []]])]
        for pid, args in bad:
            with self.assertRaises(ValueError):
                o.validate(pid, args)

    def test_strict_return_types_and_void(self):
        args = trace(2526, [1, 1], [('consec', [1])]); self.assertFalse(o.valid_answer(2526, args, [None, 1])); self.assertTrue(o.valid_answer(2526, args, [None, True]))
        args = trace(2671, [], [('add', [1])]); self.assertFalse(o.valid_answer(2671, args, [None, False]))
        args = trace(2502, [1], [('allocate', [1, 1])]); self.assertFalse(o.valid_answer(2502, args, [None, False]))
        args = trace(2642, [2, []], [('shortestPath', [0, 1])]); self.assertFalse(o.valid_answer(2642, args, [None, -1.0]))


if __name__ == '__main__':
    unittest.main()
