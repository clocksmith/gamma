"""Hack2Hire 6a97291f0ca9cc4e1c789d82 (Threshold Alerts) over an INFERRED spec; qualification unknown."""


def solve(numCalls, precedingMinutes, alertThreshold):
    k = precedingMinutes
    need = alertThreshold * k
    total = 0
    alerts = 0
    for i, v in enumerate(numCalls):
        total += v
        if i >= k:
            total -= numCalls[i - k]
        if i >= k - 1 and total >= need:
            alerts += 1
    return alerts


class Solution:
    def countAlerts(self, numCalls, precedingMinutes, alertThreshold):
        return solve(numCalls, precedingMinutes, alertThreshold)
