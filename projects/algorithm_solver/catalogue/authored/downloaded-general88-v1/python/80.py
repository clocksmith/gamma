"""80. Remove Duplicates from Sorted Array II (Medium).

Specification: https://leetcode.com/problems/remove-duplicates-from-sorted-array-ii/description/
"""


def solve(nums: list[int]) -> list[int]:
    result = []
    for value in nums:
        if len(result) < 2 or value != result[-2]:
            result.append(value)
    return result


class Solution:
    def removeDuplicates(self, nums: list[int]) -> list[int]:
        return solve(nums)
