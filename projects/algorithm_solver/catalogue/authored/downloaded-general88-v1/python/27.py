"""27. Remove Element (Easy).

Specification: https://leetcode.com/problems/remove-element/description/
"""


def solve(nums: list[int], val: int) -> list[int]:
    return [value for value in nums if value != val]


class Solution:
    def removeElement(self, nums: list[int], val: int) -> list[int]:
        return solve(nums, val)
