"""2441. Largest Positive Integer That Exists With Its Negative (Easy).

Specification: https://leetcode.com/problems/largest-positive-integer-that-exists-with-its-negative/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) expected time, O(n) space; preserve nums."""
    values = set(nums)
    result = -1
    for value in nums:
        if value > 0 and -value in values:
            result = max(result, value)
    return result


class Solution:
    def findMaxK(self, nums: list[int]) -> int:
        return solve(nums)
