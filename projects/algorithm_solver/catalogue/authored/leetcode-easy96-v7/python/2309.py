"""2309. Greatest English Letter in Upper and Lower Case (Easy).

Specification: https://leetcode.com/problems/greatest-english-letter-in-upper-and-lower-case/description/
"""


def solve(s: str) -> str:
    """O(n) time, O(1) alphabet space; search Z through A for both cases."""
    present = set(s)
    for code in range(90, 64, -1):
        upper = chr(code)
        lower = chr(code + 32)
        if upper in present and lower in present:
            return upper
    return ''


class Solution:
    def greatestLetter(self, s: str) -> str:
        return solve(s)
