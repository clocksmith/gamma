"""Hack2Hire 692d2a491abcca80b11223bf (Non-connected People Pairs) over an INFERRED spec; qualification unknown."""


def solve(n, connections):
    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path halving
            x = parent[x]
        return x

    for a, b in connections:
        ra, rb = find(a), find(b)
        if ra == rb:
            continue
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
    same = 0
    for v in range(n):
        if parent[v] == v:
            same += size[v] * (size[v] - 1) // 2
    return n * (n - 1) // 2 - same


class Solution:
    def countNonConnectedPairs(self, n, connections):
        return solve(n, connections)
