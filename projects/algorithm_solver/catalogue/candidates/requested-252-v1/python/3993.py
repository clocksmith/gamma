"""3993. Maximum Value of an Alternating Sequence
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-value-of-an-alternating-sequence/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3993.Maximum%20Value%20of%20an%20Alternating%20Sequence/README_EN.md
Complexity: O(1) time and space.
Use rises of m and falls of 1, with the maximum at the last possible peak. Answer is below 2^53.
"""

from __future__ import annotations

def solve(n, s, m):
    return s if n == 1 else s + (n // 2) * (m - 1) + 1


class Solution:
    def maximumValue(self, n, s, m):
        return solve(n, s, m)
