"""Original frontend 3275 variant; qualification unknown."""

import heapq


def solve(queries, k: int):
    heap = []
    out = []
    for x, y in queries:
        d = abs(x) + abs(y)
        if len(heap) < k:
            heapq.heappush(heap, -d)
        elif d < -heap[0]:
            heapq.heapreplace(heap, -d)
        out.append(-heap[0] if len(heap) == k else -1)
    return out


resultsArray = solve


class Solution:
    def resultsArray(self, queries, k: int):
        return solve(queries, k)
