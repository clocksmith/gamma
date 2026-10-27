# Original candidate. Contract: https://leetcode.com/problems/number-of-self-divisible-permutations/
def solve(n):
    from math import gcd
    dp=[0]*(1<<n);dp[0]=1
    for mask in range(1<<n):
        position=mask.bit_count()+1
        for j in range(n):
            if not mask>>j&1 and gcd(j+1,position)==1:dp[mask|1<<j]+=dp[mask]
    return dp[-1]
