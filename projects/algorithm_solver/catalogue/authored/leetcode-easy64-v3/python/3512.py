"""3512. Minimum Operations to Make Array Sum Divisible by K (Easy).

Specification: https://leetcode.com/problems/minimum-operations-to-make-array-sum-divisible-by-k/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n) time, O(1) space; reduce the positive total to its nearest lower multiple."""
    total = sum(nums)
    return total % k


class Solution:
    def minOperations(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
