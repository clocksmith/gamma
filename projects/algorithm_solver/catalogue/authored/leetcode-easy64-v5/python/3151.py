"""3151. Special Array I (Easy).

Specification: https://leetcode.com/problems/special-array-i/description/
"""


def solve(nums: list[int]) -> bool:
    """O(n) time, O(1) auxiliary space; preserve nums."""
    for index in range(1, len(nums)):
        if nums[index] % 2 == nums[index - 1] % 2:
            return False
    return True


class Solution:
    def isArraySpecial(self, nums: list[int]) -> bool:
        return solve(nums)
