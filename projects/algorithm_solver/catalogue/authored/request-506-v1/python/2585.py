# Original candidate implementation. Contract: https://leetcode.com/problems/number-of-ways-to-earn-points/
def solve(target,types):
    mod=1000000007;dp=[1]+[0]*target
    for count,marks in types:
        nxt=[0]*(target+1)
        for total in range(target+1):
            for take in range(min(count,total//marks)+1):nxt[total]=(nxt[total]+dp[total-take*marks])%mod
        dp=nxt
    return dp[target]
