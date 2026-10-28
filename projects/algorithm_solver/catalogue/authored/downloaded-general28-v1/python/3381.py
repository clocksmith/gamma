"""3381. Maximum Subarray Sum With Length Divisible by K (Medium).

Specification: https://leetcode.com/problems/maximum-subarray-sum-with-length-divisible-by-k/description/
"""


def solve(nums: list[int], k: int) -> int:
    min_prefix = [float('inf')] * k
    min_prefix[k - 1] = 0
    prefix = 0
    ans = float('-inf')
    for i, x in enumerate(nums):
        prefix += x
        ans = max(ans, prefix - min_prefix[i % k])
        min_prefix[i % k] = min(min_prefix[i % k], prefix)
    return ans


class Solution:
    def maxSubarraySum(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
