"""553. Optimal Division (Medium).

Specification: https://leetcode.com/problems/optimal-division/description/
"""


def solve(nums: list[int]) -> str:
    if len(nums) == 1:
        return str(nums[0])
    if len(nums) == 2:
        return f"{nums[0]}/{nums[1]}"
    return f"{nums[0]}/(" + "/".join(str(v) for v in nums[1:]) + ")"


class Solution:
    def optimalDivision(self, nums: list[int]) -> str:
        return solve(nums)
