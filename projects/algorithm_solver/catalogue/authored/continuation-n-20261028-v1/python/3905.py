"""Original frontend 3905 variant; qualification unknown."""

def solve(n, m, sources):
    grid = [[0] * m for _ in range(n)]
    frontier = []
    for row, col, color in sources:
        grid[row][col] = color
        frontier.append((row, col))
    while frontier:
        proposals = {}
        for row, col in frontier:
            for a, b in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if 0 <= a < n and 0 <= b < m and grid[a][b] == 0:
                    proposals[(a, b)] = max(proposals.get((a, b), 0), grid[row][col])
        frontier = list(proposals)
        for (row, col), color in proposals.items():
            grid[row][col] = color
    return grid


class Solution:
    def colorGrid(self, n, m, sources):
        return solve(n, m, sources)
