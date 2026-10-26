"""3289. The Two Sneaky Numbers of Digitville (Easy).

Specification: https://leetcode.com/problems/the-two-sneaky-numbers-of-digitville/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time and space; return repeated values in ascending order without mutation."""
    counts = [0] * (len(nums) - 2)
    for value in nums:
        counts[value] += 1
    result = []
    for value, count in enumerate(counts):
        if count == 2:
            result.append(value)
    return result


class Solution:
    def getSneakyNumbers(self, nums: list[int]) -> list[int]:
        return solve(nums)
