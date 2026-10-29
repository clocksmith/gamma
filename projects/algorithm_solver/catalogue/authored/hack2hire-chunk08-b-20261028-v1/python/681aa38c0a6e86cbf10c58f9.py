"""Hack2Hire 681aa38c0a6e86cbf10c58f9 (Shortest Hiking Distance) over an INFERRED spec; qualification unknown."""

def _days(t, limit, cap):
    count, start = 1, 0
    for i in range(1, len(t)):
        if t[i] - start > limit:
            count += 1
            if count > cap:
                return count
            start = t[i - 1]
    return count


def solve(t, k):
    n = len(t)
    if n == 1:
        return 0
    lo = 0
    for i in range(n - 1):
        if t[i + 1] - t[i] > lo:
            lo = t[i + 1] - t[i]
    hi = t[n - 1]
    while lo < hi:
        mid = (lo + hi) // 2
        if _days(t, mid, k + 1) <= k + 1:
            hi = mid
        else:
            lo = mid + 1
    return lo


class Solution:
    def minMaxDailyDistance(self, t, k):
        return solve(t, k)
