"""2915. Length of the Longest Subsequence That Sums to Target: maximize the element count for each exact sum with descending knapsack updates."""


def solve(nums: list[int], target: int) -> int:
    """O(n * target) time and O(target) auxiliary space; inputs are read-only."""
    longest = [-1] * (target + 1)
    longest[0] = 0
    for value in nums:
        for total in range(target, value - 1, -1):
            if longest[total - value] != -1:
                longest[total] = max(longest[total], longest[total - value] + 1)
    return longest[target]


class Solution:
    def lengthOfLongestSubsequence(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
