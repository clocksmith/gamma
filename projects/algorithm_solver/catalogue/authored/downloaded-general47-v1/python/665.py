"""665. Non-decreasing Array (Medium).

Specification: https://leetcode.com/problems/non-decreasing-array/description/
"""


def solve(nums: list[int]) -> bool:
    values = nums[:]
    modified = 0
    for i in range(1, len(values)):
        if values[i] < values[i - 1]:
            modified += 1
            if modified > 1:
                return False
            if i - 2 < 0 or values[i] >= values[i - 2]:
                values[i - 1] = values[i]
            else:
                values[i] = values[i - 1]
    return True


class Solution:
    def checkPossibility(self, nums: list[int]) -> bool:
        return solve(nums)
