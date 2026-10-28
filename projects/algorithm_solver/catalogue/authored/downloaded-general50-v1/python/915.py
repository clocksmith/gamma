"""915. Partition Array into Disjoint Intervals (Medium).

Specification: https://leetcode.com/problems/partition-array-into-disjoint-intervals/description/
"""


def solve(nums: list[int]) -> int:
    n = len(nums)
    right_min = [0] * n
    right_min[n - 1] = nums[n - 1]
    for i in range(n - 2, -1, -1):
        right_min[i] = min(nums[i], right_min[i + 1])
    left_max = nums[0]
    for i in range(n - 1):
        left_max = max(left_max, nums[i])
        if left_max <= right_min[i + 1]:
            return i + 1
    return n


class Solution:
    def partitionDisjoint(self, nums: list[int]) -> int:
        return solve(nums)
