"""1458. Max Dot Product of Two Subsequences (Medium).

Specification: https://leetcode.com/problems/max-dot-product-of-two-subsequences/description/
"""


def solve(nums1: list[int], nums2: list[int]) -> int:
    NEG = -10 ** 18
    dp = [[NEG] * (len(nums2) + 1) for _ in range(len(nums1) + 1)]
    for i in range(1, len(nums1) + 1):
        for j in range(1, len(nums2) + 1):
            product = nums1[i - 1] * nums2[j - 1]
            best = max(dp[i - 1][j], dp[i][j - 1], product)
            if dp[i - 1][j - 1] != NEG:
                best = max(best, dp[i - 1][j - 1] + product)
            dp[i][j] = best
    return dp[len(nums1)][len(nums2)]


class Solution:
    def maxDotProduct(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
