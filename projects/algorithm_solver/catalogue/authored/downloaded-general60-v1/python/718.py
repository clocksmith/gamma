"""718. Maximum Length of Repeated Subarray (Medium).

Specification: https://leetcode.com/problems/maximum-length-of-repeated-subarray/description/
"""


def solve(nums1: list[int], nums2: list[int]) -> int:
    m, n = len(nums1), len(nums2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    best = 0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if nums1[i - 1] == nums2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                best = max(best, dp[i][j])
    return best


class Solution:
    def findLength(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
