"""Hack2Hire 6a330d046849fecc81440a2f (Diagonal Server Redirects) over an INFERRED spec; qualification unknown."""
from bisect import bisect_left, bisect_right


def solve(locations, redirectRecords):
    main, anti = {}, {}
    for x, y in locations:
        main.setdefault(x - y, []).append(x)
        anti.setdefault(x + y, []).append(x)
    for xs in main.values():
        xs.sort()
    for xs in anti.values():
        xs.sort()
    a, b = locations[0]
    for d in redirectRecords:
        if d == 1 or d == 4:
            xs, key = main[a - b], a - b
        else:
            xs, key = anti[a + b], a + b
        if d == 1 or d == 2:
            i = bisect_right(xs, a)
            if i == len(xs):
                continue
            nx = xs[i]
        else:
            i = bisect_left(xs, a)
            if i == 0:
                continue
            nx = xs[i - 1]
        a, b = (nx, nx - key) if d in (1, 4) else (nx, key - nx)
    return [a, b]


class Solution:
    def findFinalServer(self, locations, redirectRecords):
        return solve(locations, redirectRecords)
