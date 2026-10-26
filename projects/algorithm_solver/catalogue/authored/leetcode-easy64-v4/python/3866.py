"""3866. First Unique Even Element (Easy).

Specification: https://leetcode.com/problems/first-unique-even-element/description/
"""


def solve(nums: list[int]) -> int:
    """O(n + 100) time, O(100) space; preserve nums and return the value, not its index."""
    counts = [0] * 101
    for value in nums:
        counts[value] += 1
    for value in nums:
        if value % 2 == 0 and counts[value] == 1:
            return value
    return -1


class Solution:
    def firstUniqueEven(self, nums: list[int]) -> int:
        return solve(nums)
