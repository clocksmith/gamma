"""283. Move Zeroes (Easy).

Specification: https://leetcode.com/problems/move-zeroes/description/
"""


def solve(nums: list[int]) -> list[int]:
    result = [value for value in nums if value != 0]
    while len(result) < len(nums):
        result.append(0)
    return result


class Solution:
    def moveZeroes(self, nums: list[int]) -> list[int]:
        return solve(nums)
