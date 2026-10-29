"""Hack2Hire 6818d209aa9eb23a3dba07f0 (Color a Row of Houses) over an INFERRED spec; qualification unknown."""
MOD = 1000000007


def solve(n, k, firstHouseColor, lastHouseColor):
    p = pow(k - 1, n - 1, MOD)
    sign = 1 if (n - 1) % 2 == 0 else MOD - 1
    if firstHouseColor == lastHouseColor:
        numerator = (p + (k - 1) * sign) % MOD
    else:
        numerator = (p - sign) % MOD
    return numerator * pow(k, MOD - 2, MOD) % MOD


class Solution:
    def countWays(self, n, k, firstHouseColor, lastHouseColor):
        return solve(n, k, firstHouseColor, lastHouseColor)
