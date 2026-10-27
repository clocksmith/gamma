"""3634. Minimum Removals to Balance Array.

Specification: https://leetcode.com/problems/minimum-removals-to-balance-array/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(n log n) time, O(n) space; keep the longest sorted interval with max <= k * min.
Inputs are not modified.
"""

def solve(nums, k):
    ordered = sorted(nums)
    left = 0
    longest = 0
    for right, value in enumerate(ordered):
        while value > ordered[left] * k:
            left += 1
        longest = max(longest, right - left + 1)
    return len(nums) - longest


class Solution:
    def minRemoval(self, nums, k):
        return solve(nums, k)
