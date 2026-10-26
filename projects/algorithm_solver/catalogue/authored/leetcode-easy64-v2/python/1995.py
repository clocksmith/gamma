"""1995. Count Special Quadruplets (Easy).

Specification: https://leetcode.com/problems/count-special-quadruplets/description/
"""


def solve(nums: list[int]) -> int:
    """O(n^2) expected time, O(n^2) space; pair sums only use indices before c."""
    pair_counts = {}
    result = 0
    for third in range(2, len(nums) - 1):
        second = third - 1
        for first in range(second):
            total = nums[first] + nums[second]
            pair_counts[total] = pair_counts.get(total, 0) + 1
        for fourth in range(third + 1, len(nums)):
            result += pair_counts.get(nums[fourth] - nums[third], 0)
    return result


class Solution:
    def countQuadruplets(self, nums: list[int]) -> int:
        return solve(nums)
