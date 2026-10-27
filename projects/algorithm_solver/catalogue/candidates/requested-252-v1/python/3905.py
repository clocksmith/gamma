"""3905. Multi Source Flood Fill
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/multi-source-flood-fill/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3905.Multi%20Source%20Flood%20Fill/README_EN.md
Complexity: O(n*m) time and space.
Simultaneous rounds; maximum color wins same-round ties. Distinct initial source cells. Sources preserved.
"""

from __future__ import annotations

def solve(n, m, sources):
    grid = [[0] * m for _ in range(n)]
    frontier = []
    for row, column, color in sources:
        grid[row][column] = color
        frontier.append((row, column))
    while frontier:
        pending = {}
        for row, column in frontier:
            for next_row, next_column in ((row - 1, column), (row + 1, column), (row, column - 1), (row, column + 1)):
                if 0 <= next_row < n and 0 <= next_column < m and grid[next_row][next_column] == 0:
                    key = (next_row, next_column)
                    pending[key] = max(pending.get(key, 0), grid[row][column])
        frontier = list(pending)
        for (row, column), color in pending.items():
            grid[row][column] = color
    return grid


class Solution:
    def colorGrid(self, n, m, sources):
        return solve(n, m, sources)
