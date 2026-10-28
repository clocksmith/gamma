"""1167. Minimum Cost to Connect Sticks (Medium).

Specification: https://leetcode.com/problems/minimum-cost-to-connect-sticks/description/
"""


import heapq


def solve(sticks: list[int]) -> int:
    heap = sticks[:]
    heapq.heapify(heap)
    total = 0
    while len(heap) > 1:
        first = heapq.heappop(heap)
        second = heapq.heappop(heap)
        cost = first + second
        total += cost
        heapq.heappush(heap, cost)
    return total


class Solution:
    def connectSticks(self, sticks: list[int]) -> int:
        return solve(sticks)
