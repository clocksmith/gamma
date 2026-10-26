"""3174. Clear Digits (Easy).

Specification: https://leetcode.com/problems/clear-digits/description/
"""


def solve(s: str) -> str:
    """O(n) time and space; a stack removes the closest surviving letter on the left."""
    letters = []
    for character in s:
        if '0' <= character <= '9':
            letters.pop()
        else:
            letters.append(character)
    return ''.join(letters)


class Solution:
    def clearDigits(self, s: str) -> str:
        return solve(s)
