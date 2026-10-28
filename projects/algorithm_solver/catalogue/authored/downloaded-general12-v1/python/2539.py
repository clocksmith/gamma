"""2539. Count the Number of Good Subsequences (Medium).

Specification: https://leetcode.com/problems/count-the-number-of-good-subsequences/description/
"""


def solve(s):
    MOD = 1000000007
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    vals = list(counts.values())
    mx = max(vals)
    fact = [1] * (mx + 1)
    for i in range(1, mx + 1):
        fact[i] = fact[i - 1] * i % MOD
    inv_fact = [1] * (mx + 1)
    inv_fact[mx] = pow(fact[mx], MOD - 2, MOD)
    for i in range(mx, 0, -1):
        inv_fact[i - 1] = inv_fact[i] * i % MOD

    def comb(n, k):
        if k < 0 or k > n:
            return 0
        return fact[n] * inv_fact[k] % MOD * inv_fact[n - k] % MOD

    ans = 0
    for f in range(1, mx + 1):
        prod = 1
        for c in vals:
            prod = prod * (comb(c, f) + 1) % MOD
        ans = (ans + prod - 1) % MOD
    return ans


class Solution:
    def countGoodSubsequences(self, s):
        return solve(s)
