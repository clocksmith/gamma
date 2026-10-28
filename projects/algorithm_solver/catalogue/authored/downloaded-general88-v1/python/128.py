"""128. Longest Consecutive Sequence (Medium).

Specification: https://leetcode.com/problems/longest-consecutive-sequence/description/
"""


def solve(nums: list[int]) -> int:
    seen = set(nums)
    best = 0
    for value in seen:
        if value - 1 not in seen:
            length = 1
            current = value
            while current + 1 in seen:
                current += 1
                length += 1
            best = max(best, length)
    return best


class Solution:
    def longestConsecutive(self, nums: list[int]) -> int:
        return solve(nums)
