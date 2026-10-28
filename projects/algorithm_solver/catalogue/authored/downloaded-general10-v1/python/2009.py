"""2009. Minimum Number of Operations to Make Array Continuous (Medium).

Specification: https://leetcode.com/problems/minimum-number-of-operations-to-make-array-continuous/description/
"""


def solve(nums: list[int]) -> int:
    uniq = sorted(set(nums))
    n = len(nums)
    best = 0
    right = 0
    for left in range(len(uniq)):
        while right < len(uniq) and uniq[right] - uniq[left] < n:
            right += 1
        best = max(best, right - left)
    return n - best


class Solution:
    def minOperations(self, nums: list[int]) -> int:
        return solve(nums)
