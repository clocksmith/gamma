"""2656. Maximum Sum With Exactly K Elements (Easy).

Specification: https://leetcode.com/problems/maximum-sum-with-exactly-k-elements/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n) time, O(1) auxiliary space; preserve nums."""
    largest = max(nums)
    return k * largest + k * (k - 1) // 2


class Solution:
    def maximizeSum(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
