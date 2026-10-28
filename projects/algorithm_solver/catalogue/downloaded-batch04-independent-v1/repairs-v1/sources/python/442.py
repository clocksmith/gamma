"""442. Find All Duplicates in an Array (Medium).

Specification: https://leetcode.com/problems/find-all-duplicates-in-an-array/description/
"""


def solve(nums: list[int]) -> list[int]:
    result = []
    try:
        for i in range(len(nums)):
            position = abs(nums[i]) - 1
            if nums[position] < 0:
                result.append(position + 1)
            else:
                nums[position] = -nums[position]
    finally:
        for i in range(len(nums)):
            nums[i] = abs(nums[i])
    return result


class Solution:
    def findDuplicates(self, nums: list[int]) -> list[int]:
        return solve(nums)
