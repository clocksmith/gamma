"""3922. Minimum Flips to Make Binary String Coherent
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-flips-to-make-binary-string-coherent/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3922.Minimum%20Flips%20to%20Make%20Binary%20String%20Coherent/README_EN.md
Complexity: O(n) time, O(1) space.
Coherent shapes: all ones; at most one one; or exactly two ones at the ends and zeros inside. Forbidden patterns are subsequences. Native name pending.
"""

from __future__ import annotations

def solve(s):
    ones = s.count('1')
    answer = min(len(s) - ones, max(0, ones - 1))
    if len(s) >= 2:
        two_ends = ones - int(s[0] == '1') - int(s[-1] == '1')
        two_ends += int(s[0] == '0') + int(s[-1] == '0')
        answer = min(answer, two_ends)
    return answer
