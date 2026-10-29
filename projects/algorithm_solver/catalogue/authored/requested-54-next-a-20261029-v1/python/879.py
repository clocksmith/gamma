"""Original development candidate; qualification unknown."""
def solve(n, minProfit, group, profit):
    mod = 1000000007
    dp = [[0]*(minProfit+1) for _ in range(n+1)]
    dp[0][0] = 1
    for members,gain in zip(group,profit):
        for used in range(n,members-1,-1):
            for earned in range(minProfit+1):
                target = min(minProfit,earned+gain)
                dp[used][target] = (dp[used][target]+dp[used-members][earned])%mod
    return sum(row[minProfit] for row in dp)%mod


class Solution:
    def profitableSchemes(self, n, minProfit, group, profit):
        return solve(n, minProfit, group, profit)
