"""1035. Uncrossed Lines (Medium).

Specification: https://leetcode.com/problems/uncrossed-lines/description/
"""


def solve(nums1: list[int], nums2: list[int]) -> int:
    dp = [0] * (len(nums2) + 1)
    for a in nums1:
        previous = 0
        for j, b in enumerate(nums2):
            saved = dp[j + 1]
            if a == b:
                dp[j + 1] = previous + 1
            else:
                dp[j + 1] = max(dp[j + 1], dp[j])
            previous = saved
    return dp[len(nums2)]


class Solution:
    def maxUncrossedLines(self, nums1: list[int], nums2: list[int]) -> list[int]:
        return solve(nums1, nums2)
