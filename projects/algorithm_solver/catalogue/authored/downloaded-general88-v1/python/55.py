"""55. Jump Game (Medium).

Specification: https://leetcode.com/problems/jump-game/description/
"""


def solve(nums: list[int]) -> bool:
    farthest = 0
    for i, value in enumerate(nums):
        if i > farthest:
            return False
        farthest = max(farthest, i + value)
    return True


class Solution:
    def canJump(self, nums: list[int]) -> bool:
        return solve(nums)
