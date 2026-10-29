"""Original frontend 818 variant; qualification not qualified."""

def solve(target):
    dp = [0] * (target + 1)
    for t in range(1, target + 1):
        k = t.bit_length()
        if t == (1 << k) - 1:
            dp[t] = k
            continue
        best = k + 1 + dp[(1 << k) - 1 - t]
        reached = (1 << (k - 1)) - 1
        for j in range(k - 1):
            best = min(best, k - 1 + 1 + j + 1 + dp[t - reached + (1 << j) - 1])
        dp[t] = best
    return dp[target]


class Solution:
    def racecar(self, target):
        return solve(target)
