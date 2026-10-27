"""502. IPO."""

from heapq import heappush, heappop

def solve(k: int, w: int, profits: list[int], capital: list[int]) -> int:
    projects = sorted(zip(capital, profits))
    heap = []
    index = 0
    for _ in range(k):
        while index < len(projects) and projects[index][0] <= w:
            heappush(heap, -projects[index][1])
            index += 1
        if not heap:
            break
        w -= heappop(heap)
    return w


class Solution:
    def findMaximizedCapital(self, k: int, w: int, profits: list[int], capital: list[int]) -> int:
        return solve(k, w, profits, capital)
