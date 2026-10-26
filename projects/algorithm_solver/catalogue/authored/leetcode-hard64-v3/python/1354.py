"""1354. Construct Target Array With Multiple Sums: reverse largest-value reductions with a heap; O(n) auxiliary space. Inputs are preserved."""

from heapq import heapify, heappop, heappush


def solve(target: list[int]) -> bool:
    if len(target) == 1:
        return target[0] == 1
    heap = [-value for value in target]
    heapify(heap)
    total = sum(target)
    while True:
        largest = -heappop(heap)
        remaining = total - largest
        if largest == 1 or remaining == 1:
            return True
        if remaining <= 0 or remaining >= largest:
            return False
        previous = largest % remaining
        if previous == 0:
            return False
        total = remaining + previous
        heappush(heap, -previous)


class Solution:
    def isPossible(self, target: list[int]) -> bool:
        return solve(target)
