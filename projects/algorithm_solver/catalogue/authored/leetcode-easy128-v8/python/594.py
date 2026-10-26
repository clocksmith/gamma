"""594. Longest Harmonious Subsequence (Easy).

Specification: https://leetcode.com/problems/longest-harmonious-subsequence/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) expected time, O(n) space; combine frequencies only for values differing by one."""
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    longest = 0
    for value, count in counts.items():
        if value + 1 in counts:
            longest = max(longest, count + counts[value + 1])
    return longest


class Solution:
    def findLHS(self, nums: list[int]) -> int:
        return solve(nums)
