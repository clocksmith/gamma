"""Original frontend 903 variant; qualification unknown."""

MOD = 10**9 + 7


def solve(s: str) -> int:
    dp = [1]
    for ch in s:
        if ch == "I":
            cur = 0
            ndp = []
            for x in dp:
                cur = (cur + x) % MOD
                ndp.append(cur)
            dp = ndp
        else:
            cur = 0
            ndp = [0] * (len(dp) + 1)
            for i in range(len(dp) - 1, -1, -1):
                cur = (cur + dp[i]) % MOD
                ndp[i] = cur
            dp = ndp
    return sum(dp) % MOD


numPermsDISequence = solve


class Solution:
    def numPermsDISequence(self, s: str) -> int:
        return solve(s)
