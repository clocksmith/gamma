"""Hack2Hire 68001116c48db1937ce88f45 (Count Alert Triggers) over an INFERRED spec; qualification unknown."""


def solve(errors, threshold, duration, percent):
    n = len(errors)
    if duration > n:
        return 0
    bad = 0
    for h in range(duration):
        if errors[h] > threshold:
            bad += 1
    need = percent * duration
    alerts = 1 if bad * 100 >= need else 0
    for h in range(duration, n):
        if errors[h] > threshold:
            bad += 1
        if errors[h - duration] > threshold:
            bad -= 1
        if bad * 100 >= need:
            alerts += 1
    return alerts


class Solution:
    def countAlerts(self, errors, threshold, duration, percent):
        return solve(errors, threshold, duration, percent)
