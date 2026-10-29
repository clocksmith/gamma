"""Original frontend 1230 variant; qualification unknown."""


def solve(prob, target: int) -> float:
    dp = [0.0] * (target + 1)
    dp[0] = 1.0
    for p in prob:
        for j in range(target, 0, -1):
            dp[j] = dp[j] * (1.0 - p) + dp[j - 1] * p
        dp[0] *= 1.0 - p
    return round(dp[target], 10)


probabilityOfHeads = solve


class Solution:
    def probabilityOfHeads(self, prob, target: int) -> float:
        return solve(prob, target)
