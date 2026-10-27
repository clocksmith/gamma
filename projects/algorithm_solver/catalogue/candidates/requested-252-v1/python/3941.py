"""3941. Password Strength
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/password-strength/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3941.Password%20Strength/README_EN.md
Complexity: O(n) time, O(1) bounded alphabet space.
Allowed alphabet: ASCII letters/digits and !@#$. A toy problem score, not a security-strength assessment.
"""

from __future__ import annotations

def solve(password):
    answer = 0
    for character in set(password):
        if 'a' <= character <= 'z':
            answer += 1
        elif 'A' <= character <= 'Z':
            answer += 2
        elif '0' <= character <= '9':
            answer += 3
        else:
            answer += 5
    return answer


class Solution:
    def passwordStrength(self, password):
        return solve(password)
