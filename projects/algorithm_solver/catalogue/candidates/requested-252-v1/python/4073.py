"""4073. Count Good Strings
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-good-strings/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4073.Count%20Good%20Strings/README_EN.md
Complexity: O(log n) modular operations, O(log n) bit-string space.
Good strings are exactly strings whose maximal constant-character runs all have odd length. Odd-part compositions of n number F_n; two choices of first character give 2F_n. Fast doubling with exact modular products. n<=10^15 is an exact JS Number.
"""

from __future__ import annotations

def solve(n):
    modulus = 1_000_000_007
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a*(2*b-a) % modulus
        d = (a*a+b*b) % modulus
        if bit == '0':
            a, b = c, d
        else:
            a, b = d, (c+d) % modulus
    return 2*a % modulus
