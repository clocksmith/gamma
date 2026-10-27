"""Original candidate for LeetCode 2291. Contract: https://leetcode.com/problems/maximum-profit-from-trading-stocks/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n budget) time, O(budget) space"""
def solve(present,future,budget):
    dp=[0]*(budget+1)
    for p,f in zip(present,future):
        if f>p:
            for b in range(budget,p-1,-1):dp[b]=max(dp[b],dp[b-p]+f-p)
    return dp[budget]
