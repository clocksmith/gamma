"""Hack2Hire 69953e87312381f4e70fdb95 (Maximum Vacation With Minimum Flights) over an INFERRED spec; qualification unknown."""


def _better(a_days, a_flights, b_days, b_flights):
    return a_days > b_days or (a_days == b_days and a_flights < b_flights)


def solve(days):
    m, n = len(days), len(days[0])
    d = [days[c][0] for c in range(m)]
    f = [0 if c == 0 else 1 for c in range(m)]
    for w in range(1, n):
        first = second = -1
        for c in range(m):
            if first < 0 or _better(d[c], f[c], d[first], f[first]):
                first, second = c, first
            elif second < 0 or _better(d[c], f[c], d[second], f[second]):
                second = c
        nd, nf = [0] * m, [0] * m
        for c in range(m):
            src = first if first != c else second
            bd, bf = d[c], f[c]
            if src >= 0 and _better(d[src], f[src] + 1, bd, bf):
                bd, bf = d[src], f[src] + 1
            nd[c], nf[c] = bd + days[c][w], bf
        d, f = nd, nf
    best = 0
    for c in range(1, m):
        if _better(d[c], f[c], d[best], f[best]):
            best = c
    return [d[best], f[best]]


class Solution:
    def maxVacation(self, days):
        return solve(days)
