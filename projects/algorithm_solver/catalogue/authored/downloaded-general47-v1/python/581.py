"""581. Shortest Unsorted Continuous Subarray (Medium).

Specification: https://leetcode.com/problems/shortest-unsorted-continuous-subarray/description/
"""


def solve(nums: list[int]) -> int:
    ordered = sorted(nums)
    left = len(nums)
    right = -1
    for i, value in enumerate(nums):
        if value != ordered[i]:
            left = min(left, i)
            right = max(right, i)
    return 0 if right == -1 else right - left + 1


class Solution:
    def findUnsortedSubarray(self, nums: list[int]) -> int:
        return solve(nums)
