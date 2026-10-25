"""2778. Sum of Squares of Special Elements (Easy).

Specification: https://leetcode.com/problems/sum-of-squares-of-special-elements/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; check one-based positions and preserve nums."""
    result = 0
    for index, value in enumerate(nums):
        if len(nums) % (index + 1) == 0:
            result += value * value
    return result


class Solution:
    def sumOfSquares(self, nums: list[int]) -> int:
        return solve(nums)
