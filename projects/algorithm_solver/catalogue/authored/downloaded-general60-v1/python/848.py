"""848. Shifting Letters (Medium).

Specification: https://leetcode.com/problems/shifting-letters/description/
"""


def solve(s: str, shifts: list[int]) -> str:
    chars = list(s)
    total = 0
    for i in range(len(s) - 1, -1, -1):
        total = (total + shifts[i]) % 26
        chars[i] = chr(97 + (ord(chars[i]) - 97 + total) % 26)
    return "".join(chars)


class Solution:
    def shiftingLetters(self, s: str, shifts: list[int]) -> str:
        return solve(s, shifts)
