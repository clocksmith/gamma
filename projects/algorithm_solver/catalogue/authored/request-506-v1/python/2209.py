# Original candidate. Contract: https://leetcode.com/problems/minimum-white-tiles-after-covering-with-carpets/
def solve(floor, numCarpets, carpetLen):
    n=len(floor);dp=[0]*(n+1)
    for i,c in enumerate(floor):dp[i+1]=dp[i]+int(c)
    for _ in range(numCarpets):
        nxt=[0]*(n+1)
        for i in range(1,n+1):nxt[i]=min(nxt[i-1]+int(floor[i-1]),dp[max(0,i-carpetLen)])
        dp=nxt
    return dp[n]
