"""3024. Type of Triangle (Easy).

Specification: https://leetcode.com/problems/type-of-triangle/description/
"""


def solve(nums: list[int]) -> str:
    """O(1) time and space; preserve the three side lengths."""
    first, second, third = nums
    if first + second <= third or first + third <= second or second + third <= first:
        return 'none'
    if first == second == third:
        return 'equilateral'
    if first == second or first == third or second == third:
        return 'isosceles'
    return 'scalene'


class Solution:
    def triangleType(self, nums: list[int]) -> str:
        return solve(nums)
