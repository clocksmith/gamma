"""3980. Minimum Operations to Transform Binary String
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-operations-to-transform-binary-string/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3980.Minimum%20Operations%20to%20Transform%20Binary%20String/README_EN.md
Complexity: O(n) time, O(1) auxiliary space.
A reset edge covers required 1->0 vertices. Each reset costs three operations after accounting for net bit-count change; minimum edges pair adjacent required vertices. Singletons can use either neighbor when n>1. Native method unconfirmed; solve is the explicit entry point.
"""

from __future__ import annotations

def solve(s1, s2):
    if len(s1) == 1:
        if s1 == '1' and s2 == '0':
            return -1
        return int(s1 != s2)
    baseline = resets = run = 0
    for a, b in zip(s1, s2):
        baseline += int(b) - int(a)
        if a == '1' and b == '0':
            run += 1
        else:
            resets += (run + 1) // 2
            run = 0
    resets += (run + 1) // 2
    return baseline + 3 * resets
