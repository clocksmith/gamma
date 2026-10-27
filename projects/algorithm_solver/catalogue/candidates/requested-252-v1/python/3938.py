"""3938. Maximum Path Intersection Sum in a Grid
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-path-intersection-sum-in-a-grid/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3938.Maximum%20Path%20Intersection%20Sum%20in%20a%20Grid/README_EN.md
Complexity: O(rows*columns) time, O(1) auxiliary space.
Both dimensions >=2. Shared cells at distinct columns must have equal rows (opposite vertical monotonicity); otherwise all shared cells are vertical. Boundary singleton intersections are impossible; interior singletons and all length>=2 straight segments are realizable. Native name pending.
"""

from __future__ import annotations

def solve(grid):
    rows, columns = len(grid), len(grid[0])
    answer = -float('inf')
    # Any intersection is one straight contiguous segment. Every segment
    # of length >=2 is realizable; a singleton is realizable iff interior.
    for row in range(rows):
        ending = grid[row][0]
        for column in range(1, columns):
            answer = max(answer, ending + grid[row][column])
            ending = max(grid[row][column], ending + grid[row][column])
        if 0 < row < rows - 1:
            for column in range(1, columns - 1):
                answer = max(answer, grid[row][column])
    for column in range(columns):
        ending = grid[0][column]
        for row in range(1, rows):
            answer = max(answer, ending + grid[row][column])
            ending = max(grid[row][column], ending + grid[row][column])
    return answer
