"""Hack2Hire 69a4da066e73e4abccc9c43f (Minimum Batteries for Call Duration) over an INFERRED spec; qualification unknown."""

from bisect import bisect_left


def solve(usageDuration, chargeTime, duration):
    n = len(usageDuration)
    prefix = [0]
    for u in usageDuration:
        prefix.append(prefix[-1] + u)
    total = prefix[n]
    if duration <= total:
        return bisect_left(prefix, duration)
    for i in range(n):
        if chargeTime[i] > total - usageDuration[i]:
            # pass two stops at battery i: it is still recharging when needed
            if duration <= total + prefix[i]:
                return n + bisect_left(prefix, duration - total)
            return -1
    rest = duration - total
    full = (rest - 1) // total
    return n + full * n + bisect_left(prefix, rest - full * total)


class Solution:
    def minBatteries(self, usageDuration, chargeTime, duration):
        return solve(usageDuration, chargeTime, duration)
