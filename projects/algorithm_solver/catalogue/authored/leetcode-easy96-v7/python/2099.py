"""2099. Find Subsequence of Length K With the Largest Sum (Easy).

Specification: https://leetcode.com/problems/find-subsequence-of-length-k-with-the-largest-sum/description/
"""


def solve(nums: list[int], k: int) -> list[int]:
    """O(n log n) time, O(n) space; select by value, break ties by index, then restore input order."""
    order = sorted(range(len(nums)), key=lambda index: (-nums[index], index))
    selected = sorted(order[:k])
    return [nums[index] for index in selected]


class Solution:
    def maxSubsequence(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
