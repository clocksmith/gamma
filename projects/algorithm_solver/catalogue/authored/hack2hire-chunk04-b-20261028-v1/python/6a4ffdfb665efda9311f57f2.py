"""Hack2Hire 6a4ffdfb665efda9311f57f2 (Coins and Energy) over an INFERRED spec; qualification unknown."""


def solve(initialEnergy, energy, coins):
    n = len(energy)
    cap = n
    dp = [-1] * (cap + 1)
    dp[min(initialEnergy, cap)] = 0
    best = 0
    for i in range(n):
        after = [-1] * (cap + 1)
        gain, coin = energy[i], coins[i]
        for e in range(cap + 1):
            have = dp[e]
            if have < 0:
                continue
            up = e + gain
            if up > cap:
                up = cap
            if have > after[up]:
                after[up] = have
            if have + coin > after[e]:
                after[e] = have + coin
        top = max(after)
        if top > best:
            best = top
        dp = after[1:] + [-1]
    return best


class Solution:
    def maxCoins(self, initialEnergy, energy, coins):
        return solve(initialEnergy, energy, coins)
