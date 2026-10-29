"""Hack2Hire 67d88d261989183df5382503 (Minimum Starting Battery Level) over an INFERRED spec; qualification unknown."""


def solve(usage):
    prefix = peak = 0
    for u in usage:
        prefix += u
        if prefix > peak:
            peak = prefix
    return peak + 1


class Solution:
    def minStartingBattery(self, usage):
        return solve(usage)
