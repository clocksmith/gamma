"""502. IPO (Hard).

Specification: https://leetcode.com/problems/ipo/description/
"""


def solve(k: int, w: int, profits: list[int], capital: list[int]) -> int:
    import heapq
    projects = sorted(zip(capital, profits))
    current = w
    index = 0
    affordable = []
    for _ in range(k):
        while index < len(projects) and projects[index][0] <= current:
            heapq.heappush(affordable, -projects[index][1])
            index += 1
        if not affordable:
            break
        current -= heapq.heappop(affordable)
    return current


class Solution:
    def findMaximizedCapital(self, k: int, w: int, profits: list[int], capital: list[int]) -> int:
        return solve(k, w, profits, capital)
