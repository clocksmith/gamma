"""Hack2Hire 697692bb5ed12b33b05f0f34 (Shipping Route Cost Paths, variant 3 of 3) over an INFERRED spec; qualification unknown."""

import heapq


def solve(routes, source, target):
    if source == target:
        return 0
    adjacency = {}
    for route in routes:
        a, b, _, cost = route.split(':')
        adjacency.setdefault(a, []).append((b, int(cost)))
    best = {source: 0}
    heap = [(0, source)]
    while heap:
        dist, node = heapq.heappop(heap)
        if node == target:
            return dist
        if dist > best[node]:
            continue
        for nxt, cost in adjacency.get(node, []):
            nd = dist + cost
            if nxt not in best or nd < best[nxt]:
                best[nxt] = nd
                heapq.heappush(heap, (nd, nxt))
    return -1


class Solution:
    def cheapestShippingCost(self, routes, source, target):
        return solve(routes, source, target)
