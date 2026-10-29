"""Hack2Hire 67803efe6fee41e51af73ddc (Minimum Coins to Form All Amounts) over an INFERRED spec; qualification unknown."""


def solve(coins, max):
    top = max
    kinds = sorted(set(coins))
    if kinds[0] != 1:
        return -1
    reach = 0
    count = 0
    i = 0
    n = len(kinds)
    while reach < top:
        while i < n and kinds[i] <= reach + 1:
            i += 1
        d = kinds[i - 1]
        target = top
        if i < n and kinds[i] - 1 < target:
            target = kinds[i] - 1
        steps = (target - reach + d - 1) // d
        reach += steps * d
        count += steps
    return count


class Solution:
    def minCoins(self, coins, max):
        return solve(coins, max)
