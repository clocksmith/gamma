# Original candidate. Contract: https://leetcode.com/problems/apply-operations-to-make-two-strings-equal/
def solve(s1, s2, x):
    p=[i for i,(a,b) in enumerate(zip(s1,s2)) if a!=b]
    if len(p)%2:return -1
    dp=[0]*(len(p)+1)
    for i in range(1,len(p)+1):
        dp[i]=dp[i-1]+x
        if i>=2:dp[i]=min(dp[i],dp[i-2]+2*(p[i-1]-p[i-2]))
    return dp[-1]//2
