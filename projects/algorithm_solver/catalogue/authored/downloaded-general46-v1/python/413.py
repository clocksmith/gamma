"""413. Arithmetic Slices (Medium).

Specification: https://leetcode.com/problems/arithmetic-slices/description/
"""


def solve(nums: list[int]) -> int:
    total = 0
    run = 0
    for i in range(2, len(nums)):
        if nums[i] - nums[i - 1] == nums[i - 1] - nums[i - 2]:
            run += 1
            total += run
        else:
            run = 0
    return total


class Solution:
    def numberOfArithmeticSlices(self, nums: list[int]) -> int:
        return solve(nums)
