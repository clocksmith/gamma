"""2869. Minimum Operations to Collect Elements (Easy).

Specification: https://leetcode.com/problems/minimum-operations-to-collect-elements/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n) expected time, O(k) space; inspect the suffix without removing input elements."""
    collected = set()
    for index in range(len(nums) - 1, -1, -1):
        value = nums[index]
        if 1 <= value <= k:
            collected.add(value)
        if len(collected) == k:
            return len(nums) - index
    return -1


class Solution:
    def minOperations(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
