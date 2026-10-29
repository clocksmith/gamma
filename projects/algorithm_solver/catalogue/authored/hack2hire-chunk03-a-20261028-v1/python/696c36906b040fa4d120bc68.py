"""Hack2Hire 696c36906b040fa4d120bc68 (Linear Interpolation of Missing Points) over an INFERRED spec; qualification unknown."""
from math import gcd


def ratio(num, den):
    g = gcd(abs(num), den)
    num, den = num // g, den // g
    return str(num) if den == 1 else '%d/%d' % (num, den)


def solve(interval, points):
    out = [[points[0][0], str(points[0][1])]]
    for i in range(1, len(points)):
        x1, y1 = points[i - 1]
        x2, y2 = points[i]
        gap = x2 - x1
        if gap > interval:
            for x in range(x1 + interval, x2, interval):
                out.append([x, ratio(y1 * gap + (y2 - y1) * (x - x1), gap)])
        out.append([x2, str(y2)])
    return out


class Solution:
    def fillMissingPoints(self, interval, points):
        return solve(interval, points)
