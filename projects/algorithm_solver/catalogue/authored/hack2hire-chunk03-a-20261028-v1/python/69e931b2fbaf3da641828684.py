"""Hack2Hire 69e931b2fbaf3da641828684 (Jump Game Prime) over an INFERRED spec; qualification unknown."""


def solve(nums):
    n = len(nums)
    sieve = bytearray([1]) * max(n, 2)
    sieve[0] = sieve[1] = 0
    for p in range(2, int(n ** 0.5) + 1):
        if sieve[p]:
            sieve[p * p::p] = bytearray(len(range(p * p, len(sieve), p)))
    strides = [p for p in range(3, n) if sieve[p] and p % 10 == 3]
    best = [0] * n
    best[0] = nums[0]
    for i in range(1, n):
        top = best[i - 1]
        for p in strides:
            if p > i:
                break
            if best[i - p] > top:
                top = best[i - p]
        best[i] = top + nums[i]
    return best[-1]


class Solution:
    def maxJumpScore(self, nums):
        return solve(nums)
