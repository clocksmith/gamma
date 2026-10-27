# Original candidate implementation. Contract: https://leetcode.com/problems/maximize-the-profit-as-the-salesman/
def solve(n,offers):
    ends=[[] for _ in range(n)]
    for start,end,gold in offers: ends[end].append((start,gold))
    dp=[0]*(n+1)
    for end in range(n):
        dp[end+1]=dp[end]
        for start,gold in ends[end]: dp[end+1]=max(dp[end+1],dp[start]+gold)
    return dp[n]
