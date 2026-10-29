"""Hack2Hire 69f1384f96981f58ae1f7687 (Minimum Root Edges Reversal) over an INFERRED spec; qualification unknown."""


def solve(n, fromNodes, toNodes):
    adjacency = [[] for _ in range(n + 1)]
    for a, b in zip(fromNodes, toNodes):
        adjacency[a].append((b, 0))  # walking a -> b follows the edge
        adjacency[b].append((a, 1))  # walking b -> a goes against it
    parent = [0] * (n + 1)
    along = [0] * (n + 1)
    order = [1]
    seen = [False] * (n + 1)
    seen[1] = True
    base = 0
    for u in order:
        for v, against in adjacency[u]:
            if not seen[v]:
                seen[v] = True
                parent[v] = u
                along[v] = against
                base += against
                order.append(v)
    cost = [0] * (n + 1)
    cost[1] = base
    best = base
    for v in order[1:]:
        cost[v] = cost[parent[v]] + (1 if along[v] == 0 else -1)
        if cost[v] < best:
            best = cost[v]
    return best


class Solution:
    def minEdgeReversals(self, n, fromNodes, toNodes):
        return solve(n, fromNodes, toNodes)
