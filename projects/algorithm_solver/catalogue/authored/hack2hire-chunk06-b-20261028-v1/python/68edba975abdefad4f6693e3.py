"""Hack2Hire 68edba975abdefad4f6693e3 (Grid Coloring with Boundaries) over an INFERRED spec; qualification unknown."""

def solve(grid):
    m, n = len(grid), len(grid[0])
    colour = [-1] * (m * n)
    out = [list(row) for row in grid]
    seen = [False] * (m * n)
    for first in range(m * n):
        r0, c0 = divmod(first, n)
        if seen[first] or grid[r0][c0] == -1:
            continue
        seen[first] = True
        region, head = [first], 0
        while head < len(region):
            cell = region[head]
            head += 1
            r, c = divmod(cell, n)
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= rr < m and 0 <= cc < n and grid[rr][cc] != -1 and not seen[rr * n + cc]:
                    seen[rr * n + cc] = True
                    region.append(rr * n + cc)
        base = None
        for cell in region:
            r, c = divmod(cell, n)
            if grid[r][c] != 9:
                want = grid[r][c] ^ ((r + c) & 1)
                if base is None:
                    base = want
                elif base != want:
                    return []
        if base is None:
            base = 1 ^ ((r0 + c0) & 1)
        for cell in region:
            r, c = divmod(cell, n)
            out[r][c] = base ^ ((r + c) & 1)
    return out


class Solution:
    def colorGrid(self, grid):
        return solve(grid)
