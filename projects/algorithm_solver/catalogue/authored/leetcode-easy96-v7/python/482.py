"""482. License Key Formatting (Easy).

Specification: https://leetcode.com/problems/license-key-formatting/description/
"""


def solve(s: str, k: int) -> str:
    """O(n) time and space; collect uppercase groups from the right, ignoring old separators."""
    result = []
    count = 0
    for character in reversed(s):
        if character == '-':
            continue
        if count == k:
            result.append('-')
            count = 0
        result.append(character.upper())
        count += 1
    return ''.join(reversed(result))


class Solution:
    def licenseKeyFormatting(self, s: str, k: int) -> str:
        return solve(s, k)
