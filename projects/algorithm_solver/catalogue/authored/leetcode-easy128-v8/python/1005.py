"""1005. Maximize Sum Of Array After K Negations (Easy).

Specification: https://leetcode.com/problems/maximize-sum-of-array-after-k-negations/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n log n) time, O(n) space; negate the most negative values, then handle leftover parity."""
    values = sorted(nums)
    remaining = k
    for index in range(len(values)):
        if remaining == 0 or values[index] >= 0:
            break
        values[index] = -values[index]
        remaining -= 1
    total = sum(values)
    smallest_absolute = min(abs(value) for value in values)
    return total - (remaining % 2) * 2 * smallest_absolute


class Solution:
    def largestSumAfterKNegations(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
