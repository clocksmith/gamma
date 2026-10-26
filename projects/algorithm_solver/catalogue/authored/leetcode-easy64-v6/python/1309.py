"""1309. Decrypt String from Alphabet to Integer Mapping (Easy).

Specification: https://leetcode.com/problems/decrypt-string-from-alphabet-to-integer-mapping/description/
"""


def solve(s: str) -> str:
    """O(n) time and space; consume valid one-digit or two-digit-hash tokens."""
    result = []
    index = 0
    while index < len(s):
        width = 2 if index + 2 < len(s) and s[index + 2] == '#' else 1
        value = int(s[index:index + width])
        result.append(chr(96 + value))
        index += 3 if width == 2 else 1
    return ''.join(result)


class Solution:
    def freqAlphabets(self, s: str) -> str:
        return solve(s)
