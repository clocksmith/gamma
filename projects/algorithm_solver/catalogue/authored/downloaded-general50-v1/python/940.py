"""940. Distinct Subsequences II (Hard).

Specification: https://leetcode.com/problems/distinct-subsequences-ii/description/
"""


def solve(s: str) -> int:
    MOD = 1000000007
    total = 1
    last = [0] * 26
    for ch in s:
        index = ord(ch) - 97
        previous = total
        total = (2 * total - last[index]) % MOD
        last[index] = previous
    return (total - 1) % MOD


class Solution:
    def distinctSubseqII(self, s: str) -> int:
        return solve(s)
