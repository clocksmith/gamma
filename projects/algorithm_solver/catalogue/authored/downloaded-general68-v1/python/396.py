"""396. Rotate Function (Medium).

Specification: https://leetcode.com/problems/rotate-function/description/
"""


def solve(nums: list[int]) -> int:
    n = len(nums)
    total = sum(nums)
    current = sum(i * value for i, value in enumerate(nums))
    best = current
    for i in range(1, n):
        current = current + total - n * nums[n - i]
        best = max(best, current)
    return best


class Solution:
    def maxRotateFunction(self, nums: list[int]) -> int:
        return solve(nums)
