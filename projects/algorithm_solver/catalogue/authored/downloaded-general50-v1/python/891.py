"""891. Sum of Subsequence Widths (Medium).

Specification: https://leetcode.com/problems/sum-of-subsequence-widths/description/
"""


def solve(nums: list[int]) -> int:
    MOD = 1000000007
    ordered = sorted(nums)
    n = len(ordered)
    pow2 = [1] * n
    for i in range(1, n):
        pow2[i] = pow2[i - 1] * 2 % MOD
    total = 0
    for i in range(n):
        total = (total + ordered[i] * (pow2[i] - pow2[n - 1 - i])) % MOD
    return total % MOD


class Solution:
    def sumSubseqWidths(self, nums: list[int]) -> int:
        return solve(nums)
