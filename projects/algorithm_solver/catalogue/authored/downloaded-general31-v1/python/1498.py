"""1498. Number of Subsequences That Satisfy the Given Sum Condition (Medium).

Specification: https://leetcode.com/problems/number-of-subsequences-that-satisfy-the-given-sum-condition/description/
"""


def solve(nums: list[int], target: int) -> int:
    MOD = 1000000007
    ordered = sorted(nums)
    powers = [1] * (len(ordered) + 1)
    for i in range(1, len(ordered) + 1):
        powers[i] = (powers[i - 1] * 2) % MOD
    left, right = 0, len(ordered) - 1
    count = 0
    while left <= right:
        if ordered[left] + ordered[right] <= target:
            count = (count + powers[right - left]) % MOD
            left += 1
        else:
            right -= 1
    return count


class Solution:
    def numSubseq(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
