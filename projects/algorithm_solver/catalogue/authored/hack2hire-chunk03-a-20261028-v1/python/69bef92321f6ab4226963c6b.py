"""Hack2Hire 69bef92321f6ab4226963c6b (Linear Interpolation) over an INFERRED spec; qualification unknown."""
from bisect import bisect_left
from math import gcd


def ratio(num, den):
    g = gcd(abs(num), den)
    num, den = num // g, den // g
    return str(num) if den == 1 else '%d/%d' % (num, den)


def solve(points, queries):
    high, low = {}, {}
    for x, y in points:
        if x not in high or y > high[x]:
            high[x] = y
        if x not in low or y < low[x]:
            low[x] = y
    xs = sorted(high)
    out = []
    for q in queries:
        i = bisect_left(xs, q)
        if i < len(xs) and xs[i] == q:
            out.append(str(high[q]))
        elif i == 0:
            out.append(str(low[xs[0]]))
        elif i == len(xs):
            out.append(str(high[xs[-1]]))
        else:
            x1, x2 = xs[i - 1], xs[i]
            y1, y2 = high[x1], low[x2]
            out.append(ratio(y1 * (x2 - x1) + (y2 - y1) * (q - x1), x2 - x1))
    return out


class Solution:
    def interpolate(self, points, queries):
        return solve(points, queries)
