"""Hack2Hire 68f29e6ef567e950995157ea (Snowy Mountain Path with Melting) over an INFERRED spec; qualification unknown."""


def solve(base, snow, melt):
    n = len(base)
    depth = [0] * n
    result = []
    for fall in snow:
        for i in range(n):
            v = depth[i] + fall[i] - melt
            depth[i] = v if v > 0 else 0
        total = 0
        previous = base[0] + depth[0]
        for i in range(1, n):
            height = base[i] + depth[i]
            if height > previous:
                total += height - previous
            previous = height
        result.append(total)
    return result


class Solution:
    def totalAscentByDay(self, base, snow, melt):
        return solve(base, snow, melt)
