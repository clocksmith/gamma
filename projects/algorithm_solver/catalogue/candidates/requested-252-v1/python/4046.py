"""4046. Minimum Cost Path With At Most K Turns
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-cost-path-with-at-most-k-turns/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4046.Minimum%20Cost%20Path%20With%20At%20Most%20K%20Turns/README_EN.md
Complexity: O((k+1)mn) time, O(mn) space.
At most k turns means at most k+1 straight runs. Each directional sweep minimizes over all possible starts of the final run using only the previous layer as seeds. Zero-length runs allow fewer turns; visits charge the destination each time. All four directions are supported. Inputs preserved.
"""

from __future__ import annotations

def solve(grid, k):
    rows, cols = len(grid), len(grid[0])
    cells = rows * cols
    costs = [value for row in grid for value in row]
    best = [float('inf')] * cells
    best[0] = costs[0]
    # One layer adds one straight run (possibly length zero).
    for _ in range(k+1):
        following = best.copy()
        for direction in range(4):
            work = best.copy()
            if direction < 2:
                order = range(cells) if direction == 0 else range(cells-1, -1, -1)
                step = -1 if direction == 0 else 1
                for p in order:
                    col = p % cols
                    if 0 <= col + step < cols:
                        work[p] = min(work[p], work[p+step] + costs[p])
                    following[p] = min(following[p], work[p])
            else:
                order = range(cells) if direction == 2 else range(cells-1, -1, -1)
                step = -cols if direction == 2 else cols
                for p in order:
                    if 0 <= p + step < cells:
                        work[p] = min(work[p], work[p+step] + costs[p])
                    following[p] = min(following[p], work[p])
        best = following
    return -1 if best[-1] == float('inf') else best[-1]
