"""718. Maximum Length of Repeated Subarray."""

def solve(nums1: list[int], nums2: list[int]) -> int:
    dp = [0] * (len(nums2) + 1)
    answer = 0
    for value in nums1:
        for j in range(len(nums2), 0, -1):
            dp[j] = dp[j - 1] + 1 if value == nums2[j - 1] else 0
            answer = max(answer, dp[j])
    return answer


class Solution:
    def findLength(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
