"""628. Maximum Product of Three Numbers (Easy).

Specification: https://leetcode.com/problems/maximum-product-of-three-numbers/description/
"""


def solve(nums: list[int]) -> int:
    ordered = sorted(nums)
    n = len(ordered)
    return max(ordered[n - 1] * ordered[n - 2] * ordered[n - 3], ordered[0] * ordered[1] * ordered[n - 1])


class Solution:
    def maximumProduct(self, nums: list[int]) -> int:
        return solve(nums)
