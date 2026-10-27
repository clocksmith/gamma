"""3963. Create Grid With Exactly One Path
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/create-grid-with-exactly-one-path/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3963.Create%20Grid%20With%20Exactly%20One%20Path/README_EN.md
Complexity: O(m*n) output time and space.
Returns one valid construction, not necessarily the example grid. Only the top row and final column are open.
"""

from __future__ import annotations

def solve(m, n):
    return ['.' * n] + ['#' * (n - 1) + '.' for _ in range(m - 1)]


class Solution:
    def createGrid(self, m, n):
        return solve(m, n)
