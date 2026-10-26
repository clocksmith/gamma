"""3803. Count Residue Prefixes (Easy).

Specification: https://leetcode.com/problems/count-residue-prefixes/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) lowercase alphabet space; count nonempty prefixes."""
    seen = [False] * 26
    distinct = 0
    result = 0
    for index, character in enumerate(s):
        letter = ord(character) - ord('a')
        if not seen[letter]:
            seen[letter] = True
            distinct += 1
        if distinct == (index + 1) % 3:
            result += 1
    return result


class Solution:
    def residuePrefixes(self, s: str) -> int:
        return solve(s)
