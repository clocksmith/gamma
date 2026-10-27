"""3641. Longest Semi-Repeating Subarray.

Specification: https://leetcode.com/problems/longest-semi-repeating-subarray/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(n) expected time and space; count distinct values occurring at least twice, not duplicate positions.
Inputs are not modified.
"""

def solve(nums, k):
    counts = {}
    repeated = left = best = 0
    for right, value in enumerate(nums):
        counts[value] = counts.get(value, 0) + 1
        if counts[value] == 2:
            repeated += 1
        while repeated > k:
            outgoing = nums[left]
            if counts[outgoing] == 2:
                repeated -= 1
            counts[outgoing] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


class Solution:
    def longestSubarray(self, nums, k):
        return solve(nums, k)
