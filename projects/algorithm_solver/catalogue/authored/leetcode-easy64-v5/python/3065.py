"""3065. Minimum Operations to Exceed Threshold Value I (Easy).

Specification: https://leetcode.com/problems/minimum-operations-to-exceed-threshold-value-i/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n) time, O(1) auxiliary space; preserve nums."""
    operations = 0
    for value in nums:
        if value < k:
            operations += 1
    return operations


class Solution:
    def minOperations(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
