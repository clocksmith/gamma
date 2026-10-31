"""Original frontend 3269 variant; qualification unknown."""


def solve(nums1, nums2) -> int:
    m, n = len(nums1), len(nums2)
    INF = 10**18
    dp = [INF] * (n + 1)
    dp[0] = 0
    for j in range(1, n + 1):
        p = nums2[j - 1]
        x = dp[j - 1]
        dp[j] = x + 1 + (((x + 1) ^ p) & 1)
    for i in range(1, m + 1):
        p1 = nums1[i - 1]
        ndp = [INF] * (n + 1)
        x = dp[0]
        ndp[0] = x + 1 + (((x + 1) ^ p1) & 1)
        for j in range(1, n + 1):
            p2 = nums2[j - 1]
            v1 = dp[j] + 1 + (((dp[j] + 1) ^ p1) & 1)
            v2 = ndp[j - 1] + 1 + (((ndp[j - 1] + 1) ^ p2) & 1)
            ndp[j] = v1 if v1 < v2 else v2
        dp = ndp
    return dp[n]


minLargest = solve


class Solution:
    def minLargest(self, nums1, nums2) -> int:
        return solve(nums1, nums2)
