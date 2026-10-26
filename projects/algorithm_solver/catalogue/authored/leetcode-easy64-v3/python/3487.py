"""3487. Maximum Unique Subarray Sum After Deletion (Easy).

Specification: https://leetcode.com/problems/maximum-unique-subarray-sum-after-deletion/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) expected time, O(n) space; keep distinct positives or the largest single value."""
    positive = set()
    largest = nums[0]
    total = 0
    for value in nums:
        largest = max(largest, value)
        if value > 0 and value not in positive:
            positive.add(value)
            total += value
    return total if positive else largest


class Solution:
    def maxSum(self, nums: list[int]) -> int:
        return solve(nums)
