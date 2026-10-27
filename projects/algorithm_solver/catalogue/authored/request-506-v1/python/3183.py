# Original candidate implementation. Contract: https://leetcode.com/problems/the-number-of-ways-to-make-the-sum/
def solve(n):
    mod=1000000007;dp=[1]+[0]*n
    for coin in (1,2,6):
        for total in range(coin,n+1):dp[total]=(dp[total]+dp[total-coin])%mod
    return sum(dp[n-4*c] for c in range(3) if n>=4*c)%mod
