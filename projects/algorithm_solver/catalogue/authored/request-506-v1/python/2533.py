# Original candidate implementation. Contract: https://leetcode.com/problems/number-of-good-binary-strings/
def solve(minLength,maxLength,oneGroup,zeroGroup):
    mod=1000000007;dp=[1]+[0]*maxLength
    for n in range(1,maxLength+1):
        if n>=oneGroup:dp[n]+=dp[n-oneGroup]
        if n>=zeroGroup:dp[n]+=dp[n-zeroGroup]
        dp[n]%=mod
    return sum(dp[minLength:])%mod
