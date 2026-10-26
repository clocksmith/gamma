"""268. Missing Number (Easy).

Specification: https://leetcode.com/problems/missing-number/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; sums are exact in the stated n <= 10000 domain; preserve nums."""
    missing = len(nums)
    for index, value in enumerate(nums):
        missing += index - value
    return missing


class Solution:
    def missingNumber(self, nums: list[int]) -> int:
        return solve(nums)
