"""Hack2Hire 6a7fc7a7d713d873ca7ade7b (Bubble Explosion) over an INFERRED spec; qualification unknown."""


def solve(bubbles):
    m, n = len(bubbles), len(bubbles[0])
    g = [v for row in bubbles for v in row]  # flat row-major copy
    while True:
        mark = [False] * (m * n)
        any_mark = False
        for r in range(m):
            base = r * n
            for c in range(n):
                v = g[base + c]
                if v == 0:
                    continue
                same = []
                if r > 0 and g[base - n + c] == v:
                    same.append(base - n + c)
                if r + 1 < m and g[base + n + c] == v:
                    same.append(base + n + c)
                if c > 0 and g[base + c - 1] == v:
                    same.append(base + c - 1)
                if c + 1 < n and g[base + c + 1] == v:
                    same.append(base + c + 1)
                if len(same) >= 2:
                    any_mark = True
                    mark[base + c] = True
                    for p in same:
                        mark[p] = True
        if not any_mark:
            break
        for c in range(n):
            write = m - 1
            for r in range(m - 1, -1, -1):
                p = r * n + c
                if g[p] and not mark[p]:
                    g[write * n + c] = g[p]
                    write -= 1
            while write >= 0:
                g[write * n + c] = 0
                write -= 1
    return [g[r * n:(r + 1) * n] for r in range(m)]


class Solution:
    def explodeBubbles(self, bubbles):
        return solve(bubbles)
