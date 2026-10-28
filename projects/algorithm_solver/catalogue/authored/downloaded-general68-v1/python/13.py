"""13. Roman to Integer (Easy).

Specification: https://leetcode.com/problems/roman-to-integer/description/
"""


VALUES = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}


def solve(s: str) -> int:
    total = 0
    for i, ch in enumerate(s):
        value = VALUES[ch]
        nxt = VALUES[s[i + 1]] if i + 1 < len(s) else 0
        total += -value if value < nxt else value
    return total


class Solution:
    def romanToInt(self, s: str) -> int:
        return solve(s)
