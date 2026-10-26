"""1708. Largest Subarray Length K (Easy).

Specification: https://leetcode.com/problems/largest-subarray-length-k/description/
"""


def solve(nums: list[int], k: int) -> list[int]:
    """O(n) time, O(k) result space; distinct input values make the first element decisive."""
    best_start = 0
    for start in range(1, len(nums) - k + 1):
        if nums[start] > nums[best_start]:
            best_start = start
    return nums[best_start:best_start + k]


class Solution:
    def largestSubarray(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
