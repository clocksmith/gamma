"""3423. Maximum Difference Between Adjacent Elements in a Circular Array (Easy).

Specification: https://leetcode.com/problems/maximum-difference-between-adjacent-elements-in-a-circular-array/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; include the last-to-first edge."""
    largest = abs(nums[0] - nums[-1])
    for index in range(1, len(nums)):
        largest = max(largest, abs(nums[index] - nums[index - 1]))
    return largest


class Solution:
    def maxAdjacentDistance(self, nums: list[int]) -> int:
        return solve(nums)
