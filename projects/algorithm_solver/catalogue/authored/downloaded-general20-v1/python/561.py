"""561. Array Partition (Easy).

Specification: https://leetcode.com/problems/array-partition/description/
"""


def solve(nums: list[int]) -> int:
    ordered = sorted(nums)
    return sum(ordered[index] for index in range(0, len(ordered), 2))


class Solution:
    def arrayPairSum(self, nums: list[int]) -> int:
        return solve(nums)
