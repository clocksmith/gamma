"""1099. Two Sum Less Than K (Easy).

Specification: https://leetcode.com/problems/two-sum-less-than-k/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n log n) time, O(n) space; two pointers on a sorted copy with a strict sum limit."""
    values = sorted(nums)
    left, right = 0, len(values) - 1
    best = -1
    while left < right:
        total = values[left] + values[right]
        if total < k:
            best = max(best, total)
            left += 1
        else:
            right -= 1
    return best


class Solution:
    def twoSumLessThanK(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
