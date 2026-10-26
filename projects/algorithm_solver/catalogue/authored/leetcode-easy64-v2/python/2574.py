"""2574. Left and Right Sum Differences (Easy).

Specification: https://leetcode.com/problems/left-and-right-sum-differences/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time, O(n) output space; preserve nums."""
    right = sum(nums)
    left = 0
    result = []
    for value in nums:
        right -= value
        result.append(abs(left - right))
        left += value
    return result


class Solution:
    def leftRightDifference(self, nums: list[int]) -> list[int]:
        return solve(nums)
