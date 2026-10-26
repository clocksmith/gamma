"""2717. Semi-Ordered Permutation (Easy).

Specification: https://leetcode.com/problems/semi-ordered-permutation/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) auxiliary space; preserve the permutation."""
    first = nums.index(1)
    last = nums.index(len(nums))
    return first + len(nums) - 1 - last - int(first > last)


class Solution:
    def semiOrderedPermutation(self, nums: list[int]) -> int:
        return solve(nums)
