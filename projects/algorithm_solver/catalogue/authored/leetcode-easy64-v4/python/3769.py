"""3769. Sort Integers by Binary Reflection (Easy).

Specification: https://leetcode.com/problems/sort-integers-by-binary-reflection/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n * (log M + log n)) time, O(n) space; M = max(nums); preserve nums."""
    decorated = []
    for value in nums:
        remaining = value
        reflection = 0
        while remaining > 0:
            reflection = reflection * 2 + remaining % 2
            remaining //= 2
        decorated.append((reflection, value))
    decorated.sort()
    return [value for reflection, value in decorated]


class Solution:
    def sortByReflection(self, nums: list[int]) -> list[int]:
        return solve(nums)
