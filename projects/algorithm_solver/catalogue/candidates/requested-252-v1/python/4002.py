"""4002. Count Valid Sequences
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-valid-sequences/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4002.Count%20Valid%20Sequences/README_EN.md
Complexity: O(n+log MOD) time, O(n) space.
All positive compositions minus all-odd compositions. Exact split multiplication for modular products; native method unconfirmed.
"""

from __future__ import annotations

def solve(n, k):
    mod = 1_000_000_007
    factorial = [1] * (n + 1)
    for i in range(1, n + 1):
        factorial[i] = factorial[i - 1] * i % mod
    inverse = [1] * (n + 1)
    inverse[n] = pow(factorial[n], mod - 2, mod)
    for i in range(n, 0, -1):
        inverse[i - 1] = inverse[i] * i % mod
    def choose(a, b):
        return factorial[a] * inverse[b] % mod * inverse[a - b] % mod
    answer = choose(n - 1, k - 1)
    if (n - k) % 2 == 0:
        answer -= choose((n - k) // 2 + k - 1, k - 1)
    return answer % mod
