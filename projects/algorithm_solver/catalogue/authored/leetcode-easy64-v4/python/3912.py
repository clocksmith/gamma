"""3912. Valid Elements in an Array (Easy).

Specification: https://leetcode.com/problems/valid-elements-in-an-array/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time and space; strict records on either side qualify; preserve order, duplicates, and inputs."""
    valid = [False] * len(nums)
    maximum = float('-inf')
    for index, value in enumerate(nums):
        if value > maximum:
            valid[index] = True
        maximum = max(maximum, value)
    maximum = float('-inf')
    for index in range(len(nums) - 1, -1, -1):
        if nums[index] > maximum:
            valid[index] = True
        maximum = max(maximum, nums[index])
    result = []
    for index, value in enumerate(nums):
        if valid[index]:
            result.append(value)
    return result


class Solution:
    def findValidElements(self, nums: list[int]) -> list[int]:
        return solve(nums)
