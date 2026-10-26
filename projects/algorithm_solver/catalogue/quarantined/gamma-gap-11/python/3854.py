"""3854. Minimum Operations to Make Array Parity Alternating."""
from __future__ import annotations


def solve(nums: list[int]) -> list[int]:
    """O(n log n) time and O(n) space; minimum-flip parity patterns followed by a smallest covering range of legal values."""
    n = len(nums)
    costs = [sum((value & 1) != ((index + first) & 1) for index, value in enumerate(nums)) for first in (0, 1)]
    minimum = min(costs)
    best_range = float('inf')
    for first in (0, 1):
        if costs[first] != minimum:
            continue
        options = []
        for index, value in enumerate(nums):
            if (value & 1) == ((index + first) & 1):
                options.append((value, index))
            else:
                options.append((value - 1, index))
                options.append((value + 1, index))
        options.sort()
        counts = [0] * n
        covered = 0
        left = 0
        for value, index in options:
            if counts[index] == 0:
                covered += 1
            counts[index] += 1
            while covered == n:
                best_range = min(best_range, value - options[left][0])
                dropped = options[left][1]
                counts[dropped] -= 1
                if counts[dropped] == 0:
                    covered -= 1
                left += 1
    return [minimum, best_range]


class Solution:
    def makeParityAlternating(self, nums: list[int]) -> list[int]:
        return solve(nums)
