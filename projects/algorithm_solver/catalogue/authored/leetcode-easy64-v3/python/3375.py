"""3375. Minimum Operations to Make Array Values Equal to K (Easy).

Specification: https://leetcode.com/problems/minimum-operations-to-make-array-values-equal-to-k/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n) expected time and O(n) space; count distinct levels strictly above k."""
    levels = set()
    for value in nums:
        if value < k:
            return -1
        if value > k:
            levels.add(value)
    return len(levels)


class Solution:
    def minOperations(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
