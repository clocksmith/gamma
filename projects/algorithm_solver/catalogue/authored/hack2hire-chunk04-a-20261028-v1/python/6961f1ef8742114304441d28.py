"""Hack2Hire 6961f1ef8742114304441d28 (Target Stock Portfolio Operations) over an INFERRED spec; qualification unknown."""

MOD = 10**9 + 7


def solve(initial, target, m):
    width = max(initial, target) + m + 2
    ways = [0] * width
    ways[initial] = 1
    total = ways[target]
    for step in range(1, m + 1):
        top = min(initial + step, target + m - step, width - 2)
        nxt = [0] * width
        for h in range(top + 1):
            value = ways[h + 1]
            if h:
                value += ways[h - 1]
            nxt[h] = value % MOD
        ways = nxt
        total = (total + ways[target]) % MOD
    return total


class Solution:
    def countWays(self, initial, target, m):
        return solve(initial, target, m)
