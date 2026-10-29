"""Hack2Hire 681bafaba73bd75b806cb981 (Count Objects in Pin) over an INFERRED spec; qualification unknown."""


def solve(grid, objectIds):
    rows, cols = len(grid), len(grid[0])

    def is_same_object(r1, c1, r2, c2):
        return grid[r1][c1] == '*' and grid[r2][c2] == '*' and objectIds[r1][c1] == objectIds[r2][c2]
    seen = bytearray(rows * cols)
    objects = 0
    for start in range(rows * cols):
        r0, c0 = divmod(start, cols)
        if seen[start] or grid[r0][c0] != '*':
            continue
        objects += 1
        seen[start] = 1
        queue = [start]
        head = 0
        while head < len(queue):
            r, c = divmod(queue[head], cols)
            head += 1
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < rows and 0 <= nc < cols:
                    nxt = nr * cols + nc
                    if not seen[nxt] and is_same_object(r, c, nr, nc):
                        seen[nxt] = 1
                        queue.append(nxt)
    return objects


class Solution:
    def countObjects(self, grid, objectIds):
        return solve(grid, objectIds)
