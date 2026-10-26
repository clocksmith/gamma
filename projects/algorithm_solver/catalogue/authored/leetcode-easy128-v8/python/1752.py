"""1752. Check if Array Is Sorted and Rotated (Easy).

Specification: https://leetcode.com/problems/check-if-array-is-sorted-and-rotated/description/
"""


def solve(nums: list[int]) -> bool:
    """O(n) time, O(1) space; a circular nondecreasing array has at most one strict drop."""
    drops = 0
    for index, value in enumerate(nums):
        if value > nums[(index + 1) % len(nums)]:
            drops += 1
            if drops > 1:
                return False
    return True


class Solution:
    def check(self, nums: list[int]) -> bool:
        return solve(nums)
