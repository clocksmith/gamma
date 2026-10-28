"""414. Third Maximum Number (Easy).

Specification: https://leetcode.com/problems/third-maximum-number/description/
"""


def solve(nums: list[int]) -> int:
    distinct = sorted(set(nums), reverse=True)
    return distinct[2] if len(distinct) >= 3 else distinct[0]


class Solution:
    def thirdMax(self, nums: list[int]) -> int:
        return solve(nums)
