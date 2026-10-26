"""3266. Final Array State After K Multiplication Operations II.

Simulate until every multiplication exceeds the initial maximum, then apply sorted cycles with modular powers; O((n+R) log n+n log k) time and O(n) space. Inputs are preserved.
"""

import heapq


def solve(nums: list[int], k: int, multiplier: int) -> list[int]:
    modulus = 1_000_000_007
    if multiplier == 1:
        return [value % modulus for value in nums]
    ceiling = max(nums)
    heap = [(value, index) for index, value in enumerate(nums)]
    heapq.heapify(heap)
    while k and heap[0][0] * multiplier <= ceiling:
        value, index = heapq.heappop(heap)
        heapq.heappush(heap, (value * multiplier, index))
        k -= 1
    rounds, extra = divmod(k, len(nums))
    factor = pow(multiplier, rounds, modulus)
    answer = [0] * len(nums)
    for position, (value, index) in enumerate(sorted(heap)):
        answer[index] = value % modulus * factor % modulus
        if position < extra:
            answer[index] = answer[index] * multiplier % modulus
    return answer


class Solution:
    def getFinalState(self, nums: list[int], k: int, multiplier: int) -> list[int]:
        return solve(nums, k, multiplier)
