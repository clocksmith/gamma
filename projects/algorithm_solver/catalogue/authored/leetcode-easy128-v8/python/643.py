"""643. Maximum Average Subarray I (Easy).

Specification: https://leetcode.com/problems/maximum-average-subarray-i/description/
"""


def solve(nums: list[int], k: int) -> float:
    """O(n) time, O(1) auxiliary space; maintain the exact integer sum of each k-wide window."""
    total = 0
    for index in range(k):
        total += nums[index]
    largest = total
    for index in range(k, len(nums)):
        total += nums[index] - nums[index - k]
        largest = max(largest, total)
    return largest / k


class Solution:
    def findMaxAverage(self, nums: list[int], k: int) -> float:
        return solve(nums, k)
