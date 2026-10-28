"""2902. Count of Sub-Multisets With Bounded Sum (Hard).

Specification: https://leetcode.com/problems/count-of-sub-multisets-with-bounded-sum/description/
"""


def solve(nums, l, r):
    MOD = 1000000007
    zeros = 0
    freq = {}
    for x in nums:
        if x == 0:
            zeros += 1
        else:
            freq[x] = freq.get(x, 0) + 1
    dp = [0] * (r + 1)
    dp[0] = 1
    for v, f in freq.items():
        ndp = [0] * (r + 1)
        for rem in range(v):
            window = 0
            t = 0
            s = rem
            while s <= r:
                window = (window + dp[s]) % MOD
                if t > f:
                    window = (window - dp[s - (f + 1) * v]) % MOD
                ndp[s] = window
                s += v
                t += 1
        dp = ndp
    ans = sum(dp[l:r + 1]) % MOD
    return (ans * (zeros + 1)) % MOD


class Solution:
    def countSubMultisets(self, *args):
        return solve(*args)
