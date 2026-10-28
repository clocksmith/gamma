"""410. Split Array Largest Sum (Hard).

Specification: https://leetcode.com/problems/split-array-largest-sum/description/
"""


def _can_split(nums, k, limit):
    parts = 1
    total = 0
    for value in nums:
        if total + value > limit:
            parts += 1
            total = value
        else:
            total += value
    return parts <= k


def solve(nums: list[int], k: int) -> int:
    left = max(nums)
    right = sum(nums)
    while left < right:
        mid = (left + right) // 2
        if _can_split(nums, k, mid):
            right = mid
        else:
            left = mid + 1
    return left


class Solution:
    def splitArray(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
