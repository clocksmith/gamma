"""2529. Maximum Count of Positive Integer and Negative Integer (Easy).

Specification: https://leetcode.com/problems/maximum-count-of-positive-integer-and-negative-integer/description/
"""


def solve(nums: list[int]) -> int:
    """O(log n) time, O(1) space; nums is sorted and contains integers."""
    def lower_bound(target: int) -> int:
        low, high = 0, len(nums)
        while low < high:
            middle = (low + high) // 2
            if nums[middle] < target:
                low = middle + 1
            else:
                high = middle
        return low

    negatives = lower_bound(0)
    positives = len(nums) - lower_bound(1)
    return max(negatives, positives)


class Solution:
    def maximumCount(self, nums: list[int]) -> int:
        return solve(nums)
