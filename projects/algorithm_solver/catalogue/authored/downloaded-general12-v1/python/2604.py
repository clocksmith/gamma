"""2604. Minimum Time to Eat All Grains (Hard).

Specification: https://leetcode.com/problems/minimum-time-to-eat-all-grains/description/
"""


def solve(hens, grains):
    h = sorted(hens)
    g = sorted(grains)
    m = len(g)

    def check(t):
        j = 0
        for x in h:
            if j == m:
                return True
            y = g[j]
            if y <= x:
                d = x - y
                if d > t:
                    return False
                while j < m and g[j] <= x:
                    j += 1
                while j < m and min(d, g[j] - x) + g[j] - y <= t:
                    j += 1
            else:
                while j < m and g[j] - x <= t:
                    j += 1
        return j == m

    lo = 0
    hi = abs(h[0] - g[0]) + g[m - 1] - g[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if check(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


class Solution:
    def minimumTime(self, hens, grains):
        return solve(hens, grains)
