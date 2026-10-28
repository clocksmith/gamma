"""283. Move Zeroes (Easy).

Specification: https://leetcode.com/problems/move-zeroes/description/
"""


def solve(nums: list[int]) -> list[int]:
    result = [value for value in nums if value != 0]
    while len(result) < len(nums):
        result.append(0)
    return result


class Solution:
    def moveZeroes(self, nums: list[int]) -> None:
        write = 0
        for value in nums:
            if value != 0:
                nums[write] = value
                write += 1
        for index in range(write, len(nums)):
            nums[index] = 0
