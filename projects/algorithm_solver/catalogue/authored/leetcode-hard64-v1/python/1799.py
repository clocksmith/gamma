"""1799. Maximize Score After N Operations: pair GCD preprocessing and subset dynamic programming."""

from math import gcd


def solve(nums: list[int]) -> int:
    """O(n^2 * 2^n + n^2*log M) time and O(2^n + n^2) space. Inputs are preserved."""
    length = len(nums)
    common = [[0] * length for _ in nums]
    for first in range(length):
        for second in range(first + 1, length):
            common[first][second] = gcd(nums[first], nums[second])
    size = 1 << length
    best = [-1] * size
    best[0] = 0
    for mask in range(size):
        used = mask.bit_count()
        if used % 2 or best[mask] < 0:
            continue
        operation = used // 2 + 1
        for first in range(length):
            if mask & (1 << first):
                continue
            for second in range(first + 1, length):
                if mask & (1 << second):
                    continue
                following = mask | (1 << first) | (1 << second)
                best[following] = max(best[following], best[mask] + operation * common[first][second])
    return best[-1]


class Solution:
    def maxScore(self, nums: list[int]) -> int:
        return solve(nums)
