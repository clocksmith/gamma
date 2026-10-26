"""3028. Ant on the Boundary (Easy).

Specification: https://leetcode.com/problems/ant-on-the-boundary/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; count returns after complete moves, excluding the start."""
    position = 0
    result = 0
    for movement in nums:
        position += movement
        if position == 0:
            result += 1
    return result


class Solution:
    def returnToBoundaryCount(self, nums: list[int]) -> int:
        return solve(nums)
