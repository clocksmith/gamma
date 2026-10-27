"""3990. Create Grid With Exactly K Paths II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/create-grid-with-exactly-k-paths-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3990.Create%20Grid%20With%20Exactly%20K%20Paths%20II/README_EN.md
Complexity: O(log^2 k) time and output space.
A diagonal chain of 2x2 diamonds doubles counts; isolated horizontal exits add selected powers of two to a right-hand collector. For k<=1000 the grid is at most 19x21. Native method unconfirmed.
"""

from __future__ import annotations

def solve(k):
    bits = k.bit_length()
    height, width = 2 * bits - 1, 2 * bits + 1
    grid = [['#'] * width for _ in range(height)]
    for row in range(height):
        grid[row][-1] = '.'
    for bit in range(bits):
        p = 2 * bit
        grid[p][p] = '.'
        if bit + 1 < bits:
            grid[p][p + 1] = '.'
            grid[p + 1][p] = grid[p + 1][p + 1] = '.'
            grid[p + 2][p + 1] = '.'
        if k & (1 << bit):
            for col in range(p + 1, width):
                grid[p][col] = '.'
    return [''.join(row) for row in grid]
