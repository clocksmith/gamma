"""1911. Maximum Alternating Subsequence Sum: track the best alternating sum for each final sign."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    added = subtracted = 0
    for value in nums:
        next_added = max(added, subtracted + value)
        next_subtracted = max(subtracted, added - value)
        added, subtracted = next_added, next_subtracted
    return added


class Solution:
    def maxAlternatingSum(self, nums: list[int]) -> int:
        return solve(nums)
