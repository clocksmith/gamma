# Original candidate. Contract: https://leetcode.com/problems/equalize-strings-by-adding-or-removing-characters-at-ends/
def solve(initial, target):
    dp=[0]*(len(target)+1);best=0
    for a in initial:
        previous=0
        for j,b in enumerate(target,1):
            old=dp[j];dp[j]=previous+1 if a==b else 0;previous=old;best=max(best,dp[j])
    return len(initial)+len(target)-2*best
