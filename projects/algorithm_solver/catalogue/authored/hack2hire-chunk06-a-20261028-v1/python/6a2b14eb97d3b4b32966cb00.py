"""Hack2Hire 6a2b14eb97d3b4b32966cb00 (Factory Network Cost Minimization, variant 3 of 3) over an INFERRED spec; qualification unknown."""
INF = float('inf')


def solve(costs, edges):
    n = len(costs)
    adjacent = [[] for _ in range(n)]
    for u, v in edges:
        adjacent[u].append(v)
        adjacent[v].append(u)
    parent = [-1] * n
    order, stack = [], [0]
    seen = [False] * n
    seen[0] = True
    while stack:
        v = stack.pop()
        order.append(v)
        for w in adjacent[v]:
            if not seen[w]:
                seen[w] = True
                parent[w] = v
                stack.append(w)
    best1, index1, best2 = [INF] * n, [-1] * n, [INF] * n
    base = [0] * n
    extra = [None] * n
    for v in reversed(order):
        row, b1, i1, b2 = costs[v], INF, -1, INF
        add = extra[v] or {}
        for j, cost in enumerate(row):
            value = cost + base[v] + add.get(j, 0)
            if value < b1:
                b1, i1, b2 = value, j, b1
            elif value < b2:
                b2 = value
        if b1 == INF:
            return -1
        best1[v], index1[v], best2[v] = b1, i1, b2
        p = parent[v]
        if p >= 0:
            base[p] += b1
            if extra[p] is None:
                extra[p] = {}
            extra[p][i1] = extra[p].get(i1, 0) + (b2 - b1)
    return best1[0]


class Solution:
    def minimumCost(self, costs, edges):
        return solve(costs, edges)
