"""26. Remove Duplicates from Sorted Array (Easy).

Specification: https://leetcode.com/problems/remove-duplicates-from-sorted-array/description/
"""


def solve(nums: list[int]) -> list[int]:
    if not nums:
        return []
    result = [nums[0]]
    for i in range(1, len(nums)):
        if nums[i] != nums[i - 1]:
            result.append(nums[i])
    return result


class Solution:
    def removeDuplicates(self, nums: list[int]) -> list[int]:
        return solve(nums)
