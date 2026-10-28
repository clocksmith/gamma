"""215. Kth Largest Element in an Array (Medium).

Specification: https://leetcode.com/problems/kth-largest-element-in-an-array/description/
"""


def solve(nums: list[int], k: int) -> int:
    return sorted(nums, reverse=True)[k - 1]


class Solution:
    def findKthLargest(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
