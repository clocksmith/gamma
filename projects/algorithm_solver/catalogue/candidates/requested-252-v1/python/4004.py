"""4004. Minimum Moves to Balance Circular Array II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-moves-to-balance-circular-array-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4004.Minimum%20Moves%20to%20Balance%20Circular%20Array%20II/README_EN.md
Complexity: O(A*n*log n) time for A bottleneck augmentations, O(n) space.
Min-cost flow on the bidirectional cycle with feasible reduced-cost potentials; aggregate capacities, not unit transfers. Maximum-size runtime not measured. Inputs preserved.
"""

from __future__ import annotations
from heapq import heappop, heappush

def solve(balance):
    if sum(balance) < 0:
        return -1
    need = sum(-value for value in balance if value < 0)
    if need == 0:
        return 0
    n = len(balance)
    source, sink, size = n, n + 1, n + 2
    graph = [[] for _ in range(size)]
    def edge(u, v, capacity, cost):
        graph[u].append([v, capacity, cost, len(graph[v])])
        graph[v].append([u, 0, -cost, len(graph[u]) - 1])
    for i, value in enumerate(balance):
        if value > 0:
            edge(source, i, value, 0)
        elif value < 0:
            edge(i, sink, -value, 0)
        for j in {(i - 1) % n, (i + 1) % n}:
            edge(i, j, need, 1)
    potential = [0] * size
    answer = 0
    while need:
        distance = [float('inf')] * size
        previous = [None] * size
        distance[source] = 0
        queue = [(0, source)]
        while queue:
            d, u = heappop(queue)
            if d != distance[u]:
                continue
            for index, (v, capacity, cost, reverse) in enumerate(graph[u]):
                candidate = d + cost + potential[u] - potential[v]
                if capacity > 0 and candidate < distance[v]:
                    distance[v] = candidate
                    previous[v] = (u, index)
                    heappush(queue, (candidate, v))
        if previous[sink] is None:
            return -1
        for v in range(size):
            if distance[v] < float('inf'):
                potential[v] += distance[v]
        amount, v = need, sink
        while v != source:
            u, index = previous[v]
            amount = min(amount, graph[u][index][1])
            v = u
        v = sink
        while v != source:
            u, index = previous[v]
            e = graph[u][index]
            answer += amount * e[2]
            e[1] -= amount
            graph[v][e[3]][1] += amount
            v = u
        need -= amount
    return answer


class Solution:
    def minMoves(self, balance):
        return solve(balance)
