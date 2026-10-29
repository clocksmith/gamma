"""Hack2Hire 6866f15ea2d59460201f2c7e (Matrix Escape) over an INFERRED spec; qualification unknown."""


def solve(grid):
    m, n = len(grid), len(grid[0])
    flat = ''.join(grid)
    size = m * n
    inf = size + 1
    threat = [inf] * size
    queue = [i for i in range(size) if flat[i] == 'P']
    for i in queue:
        threat[i] = 0

    def neighbours(i):
        r, c = divmod(i, n)
        if r > 0: yield i - n
        if r < m - 1: yield i + n
        if c > 0: yield i - 1
        if c < n - 1: yield i + 1
    head = 0
    while head < len(queue):
        i = queue[head]
        head += 1
        for j in neighbours(i):
            if flat[j] != 'X' and threat[j] == inf:
                threat[j] = threat[i] + 1
                queue.append(j)
    start = flat.index('U')
    time = [-1] * size
    time[start] = 0
    queue, head = [start], 0
    while head < len(queue):
        i = queue[head]
        head += 1
        r, c = divmod(i, n)
        if r == 0 or c == 0 or r == m - 1 or c == n - 1:
            return time[i]
        for j in neighbours(i):
            if flat[j] != 'X' and time[j] < 0 and time[i] + 1 < threat[j]:
                time[j] = time[i] + 1
                queue.append(j)
    return -1


class Solution:
    def escapeMatrix(self, grid):
        return solve(grid)
