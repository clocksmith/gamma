"""1626. Best Team With No Conflicts (Medium).

Specification: https://leetcode.com/problems/best-team-with-no-conflicts/description/
"""


def solve(scores: list[int], ages: list[int]) -> int:
    players = sorted(zip(ages, scores))
    dp = [0] * len(players)
    best = 0
    for i in range(len(players)):
        dp[i] = players[i][1]
        for j in range(i):
            if players[j][1] <= players[i][1]:
                dp[i] = max(dp[i], dp[j] + players[i][1])
        best = max(best, dp[i])
    return best


class Solution:
    def bestTeamScore(self, scores: list[int], ages: list[int]) -> int:
        return solve(scores, ages)
