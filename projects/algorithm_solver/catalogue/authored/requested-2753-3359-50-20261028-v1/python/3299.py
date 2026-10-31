"""Original frontend 3299 variant; qualification unknown."""

from collections import defaultdict

MOD = 10**9 + 7


def solve(nums) -> int:
    def calc(step: int) -> int:
        cnt = defaultdict(int)
        tot = defaultdict(int)
        ans = 0
        for x in nums:
            nc = (1 + cnt[x - step]) % MOD
            nt = (tot[x - step] + nc * x) % MOD
            ans = (ans + nt) % MOD
            cnt[x] = (cnt[x] + nc) % MOD
            tot[x] = (tot[x] + nt) % MOD
        return ans

    return (calc(1) + calc(-1) - sum(nums)) % MOD


getSum = solve


class Solution:
    def getSum(self, nums) -> int:
        return solve(nums)
