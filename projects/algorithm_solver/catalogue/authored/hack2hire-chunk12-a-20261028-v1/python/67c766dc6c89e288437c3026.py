"""Hack2Hire 67c766dc6c89e288437c3026 (Maximum Building Height) over an INFERRED spec; qualification unknown."""


def solve(grid):
    m, n = len(grid), len(grid[0])
    flat = ''.join(grid)
    dist = [-1] * (m * n)
    queue = [i for i, ch in enumerate(flat) if ch == 'P']
    for i in queue:
        dist[i] = 0
    head = 0
    while head < len(queue):
        i = queue[head]
        head += 1
        r, c = divmod(i, n)
        for j, ok in ((i - n, r > 0), (i + n, r < m - 1), (i - 1, c > 0), (i + 1, c < n - 1)):
            if ok and dist[j] < 0 and flat[j] != 'X':
                dist[j] = dist[i] + 1
                queue.append(j)
    best = 0
    for i, ch in enumerate(flat):
        if ch == '-':
            if dist[i] < 0:
                return -1
            if dist[i] > best:
                best = dist[i]
    return best


class Solution:
    def maxBuildingHeight(self, grid):
        return solve(grid)
