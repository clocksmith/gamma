"""3988. Create Grid With Exactly K Paths I
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/create-grid-with-exactly-k-paths-i/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3988.Create%20Grid%20With%20Exactly%20K%20Paths%20I/README_EN.md
Complexity: O(m*n) time and output space.
Constructs 2-by-k path-count gadget or a 3-by-3 four-path gadget; a single exit corridor preserves the count. Complete for stated 1<=k<=4. Native method unconfirmed.
"""

from __future__ import annotations

def solve(m, n, k):
    grid = [['#'] * n for _ in range(m)]
    if k == 1:
        height = width = 1
        grid[0][0] = '.'
    elif m >= 2 and n >= k:
        height, width = 2, k
        for i in range(height):
            for j in range(width):
                grid[i][j] = '.'
    elif n >= 2 and m >= k:
        height, width = k, 2
        for i in range(height):
            for j in range(width):
                grid[i][j] = '.'
    elif k == 4 and m >= 3 and n >= 3:
        height = width = 3
        for i in range(3):
            for j in range(3):
                if (i, j) not in ((0, 2), (2, 0)):
                    grid[i][j] = '.'
    else:
        return []
    for i in range(height - 1, m):
        grid[i][width - 1] = '.'
    for j in range(width - 1, n):
        grid[m - 1][j] = '.'
    return [''.join(row) for row in grid]
