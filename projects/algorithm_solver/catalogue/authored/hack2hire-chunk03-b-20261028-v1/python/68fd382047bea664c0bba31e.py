"""Hack2Hire 68fd382047bea664c0bba31e (Non-Consecutive Process Scheduling) over an INFERRED spec; qualification unknown."""

MOD = 1_000_000_007


def solve(nProcesses, nIntervals):
    result, base, exponent = nProcesses % MOD, (nProcesses - 1) % MOD, nIntervals - 1
    while exponent:
        if exponent & 1: result = result * base % MOD
        base = base * base % MOD
        exponent >>= 1
    return result


class Solution:
    def countSchedules(self, nProcesses, nIntervals):
        return solve(nProcesses, nIntervals)
