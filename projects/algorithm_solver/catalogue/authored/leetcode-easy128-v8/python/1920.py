"""1920. Build Array from Permutation (Easy).

Specification: https://leetcode.com/problems/build-array-from-permutation/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time and space; read each composed index from the unchanged input permutation."""
    return [nums[value] for value in nums]


class Solution:
    def buildArray(self, nums: list[int]) -> list[int]:
        return solve(nums)
