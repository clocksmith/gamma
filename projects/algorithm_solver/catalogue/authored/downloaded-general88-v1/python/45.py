"""45. Jump Game II (Medium).

Specification: https://leetcode.com/problems/jump-game-ii/description/
"""


def solve(nums: list[int]) -> int:
    jumps = 0
    current_end = 0
    farthest = 0
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == current_end:
            jumps += 1
            current_end = farthest
    return jumps


class Solution:
    def jump(self, nums: list[int]) -> int:
        return solve(nums)
