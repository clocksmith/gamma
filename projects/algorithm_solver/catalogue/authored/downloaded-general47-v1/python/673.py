"""673. Number of Longest Increasing Subsequence (Medium).

Specification: https://leetcode.com/problems/number-of-longest-increasing-subsequence/description/
"""


def solve(nums: list[int]) -> int:
    lengths = [1] * len(nums)
    counts = [1] * len(nums)
    longest = 1
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                if lengths[j] + 1 > lengths[i]:
                    lengths[i] = lengths[j] + 1
                    counts[i] = counts[j]
                elif lengths[j] + 1 == lengths[i]:
                    counts[i] += counts[j]
        longest = max(longest, lengths[i])
    total = 0
    for i in range(len(nums)):
        if lengths[i] == longest:
            total += counts[i]
    return total


class Solution:
    def findNumberOfLIS(self, nums: list[int]) -> int:
        return solve(nums)
