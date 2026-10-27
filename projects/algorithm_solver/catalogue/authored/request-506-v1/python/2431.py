# Original implementation. Contract: https://leetcode.com/problems/maximize-total-tastiness-of-purchased-fruits/
def solve(price,tastiness,maxAmount,maxCoupons):
    dp=[[0]*(maxAmount+1) for _ in range(maxCoupons+1)]
    for p,t in zip(price,tastiness):
        old=dp;dp=[row[:] for row in old]
        for c in range(maxCoupons+1):
            for money in range(maxAmount+1):
                if money>=p:dp[c][money]=max(dp[c][money],old[c][money-p]+t)
                if c and money>=p//2:dp[c][money]=max(dp[c][money],old[c-1][money-p//2]+t)
    return dp[-1][-1]
