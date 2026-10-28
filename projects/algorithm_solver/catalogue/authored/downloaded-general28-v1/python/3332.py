"""3332. Maximum Points Tourist Can Earn (Medium).

Specification: https://leetcode.com/problems/maximum-points-tourist-can-earn/description/
"""


def solve(n: int, k: int, stayScore: list[list[int]], travelScore: list[list[int]]) -> int:
    dp = [0] * n
    for day in range(k):
        ndp = [float('-inf')] * n
        for dest in range(n):
            best = dp[dest] + stayScore[day][dest]
            for curr in range(n):
                if curr != dest:
                    best = max(best, dp[curr] + travelScore[curr][dest])
            ndp[dest] = best
        dp = ndp
    return max(dp)


class Solution:
    def maxScore(self, n: int, k: int, stayScore: list[list[int]], travelScore: list[list[int]]) -> int:
        return solve(n, k, stayScore, travelScore)
