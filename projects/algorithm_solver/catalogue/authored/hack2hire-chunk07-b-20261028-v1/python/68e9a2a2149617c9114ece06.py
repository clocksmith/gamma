"""Hack2Hire 68e9a2a2149617c9114ece06 (Minimize a Convex Function) over an INFERRED spec; qualification unknown."""

def solve(lines, a, b, eps):
    def value(x):
        best = None
        for slope, intercept in lines:
            v = slope * x + intercept
            if best is None or v > best:
                best = v
        return best

    lo, hi = 0, (b - a) // eps
    while lo < hi:
        mid = (lo + hi) // 2
        if value(a + mid * eps) <= value(a + (mid + 1) * eps):
            hi = mid
        else:
            lo = mid + 1
    return a + lo * eps


class Solution:
    def minimizeConvex(self, lines, a, b, eps):
        return solve(lines, a, b, eps)
