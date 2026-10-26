"""1389. Create Target Array in the Given Order (Easy).

Specification: https://leetcode.com/problems/create-target-array-in-the-given-order/description/
"""


def solve(nums: list[int], index: list[int]) -> list[int]:
    """O(n^2) time, O(n) space; insert each value at its specified current index."""
    result = []
    for position, value in enumerate(nums):
        result.insert(index[position], value)
    return result


class Solution:
    def createTargetArray(self, nums: list[int], index: list[int]) -> list[int]:
        return solve(nums, index)
