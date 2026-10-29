"""Hack2Hire 67dcd82499f4f89b276f188a (Find Shortest Path in Matrix) over an INFERRED spec; qualification unknown."""


def solve(grid):
    m, n = len(grid), len(grid[0])
    if grid[0][0] == 0 or grid[m - 1][n - 1] == 0:
        return -1
    target = m * n - 1
    distance = [-1] * (m * n)
    distance[0] = 0
    queue, head = [0], 0
    while head < len(queue):
        v = queue[head]
        head += 1
        if v == target:
            return distance[v] + 1
        r, c = divmod(v, n)
        for dr in (-1, 0, 1):
            rr = r + dr
            if rr < 0 or rr >= m:
                continue
            row = grid[rr]
            for dc in (-1, 0, 1):
                cc = c + dc
                if 0 <= cc < n and row[cc] != 0:
                    w = rr * n + cc
                    if distance[w] < 0:
                        distance[w] = distance[v] + 1
                        queue.append(w)
    return -1


class Solution:
    def shortestPath(self, grid):
        return solve(grid)
