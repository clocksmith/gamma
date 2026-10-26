"""1403. Minimum Subsequence in Non-Increasing Order (Easy).

Specification: https://leetcode.com/problems/minimum-subsequence-in-non-increasing-order/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n log n) time, O(n) space; sort a copy and require a strictly larger sum."""
    values = sorted(nums, reverse=True)
    total = sum(values)
    selected = 0
    result = []
    for value in values:
        result.append(value)
        selected += value
        if selected > total - selected:
            break
    return result


class Solution:
    def minSubsequence(self, nums: list[int]) -> list[int]:
        return solve(nums)
