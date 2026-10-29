"""Original frontend 803 variant; qualification not qualified."""

def solve(grid, hits):
    m, n = len(grid), len(grid[0])
    roof = m * n
    cells = [row[:] for row in grid]
    for r, c in hits:
        cells[r][c] = 0
    parent = list(range(roof + 1))
    size = [1] * (roof + 1)

    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    def union(a, b):
        a, b = find(a), find(b)
        if a == b:
            return
        if size[a] < size[b]:
            a, b = b, a
        parent[b] = a
        size[a] += size[b]

    def attach(r, c):
        index = r * n + c
        if r == 0:
            union(index, roof)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and cells[nr][nc]:
                union(index, nr * n + nc)

    for r in range(m):
        for c in range(n):
            if cells[r][c]:
                attach(r, c)
    answer = [0] * len(hits)
    for k in range(len(hits) - 1, -1, -1):
        r, c = hits[k]
        if not grid[r][c]:
            continue
        before = size[find(roof)]
        cells[r][c] = 1
        attach(r, c)
        answer[k] = max(0, size[find(roof)] - before - 1)
    return answer


class Solution:
    def hitBricks(self, grid, hits):
        return solve(grid, hits)
