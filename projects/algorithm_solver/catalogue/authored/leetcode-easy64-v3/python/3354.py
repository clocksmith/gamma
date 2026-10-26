"""3354. Make Array Elements Equal to Zero (Easy).

Specification: https://leetcode.com/problems/make-array-elements-equal-to-zero/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; compare mass on each side of every zero without simulation."""
    total = sum(nums)
    left = 0
    result = 0
    for value in nums:
        if value == 0:
            difference = abs(left - (total - left))
            if difference == 0:
                result += 2
            elif difference == 1:
                result += 1
        left += value
    return result


class Solution:
    def countValidSelections(self, nums: list[int]) -> int:
        return solve(nums)
