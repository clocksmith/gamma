"""Original frontend 3351 variant; qualification unknown."""

from collections import defaultdict

MOD = 10**9 + 7


def solve(nums) -> int:
    cnt = defaultdict(int)
    tot = defaultdict(int)
    for x in nums:
        nc = (1 + cnt[x - 1] + cnt[x + 1]) % MOD
        nt = (tot[x - 1] + tot[x + 1] + nc * x) % MOD
        cnt[x] = (cnt[x] + nc) % MOD
        tot[x] = (tot[x] + nt) % MOD
    return sum(tot.values()) % MOD


sumOfGoodSubsequences = solve


class Solution:
    def sumOfGoodSubsequences(self, nums) -> int:
        return solve(nums)
