"""3823. Reverse Letters Then Special Characters in a String (Easy).

Specification: https://leetcode.com/problems/reverse-letters-then-special-characters-in-a-string/description/
"""


def solve(s: str) -> str:
    """O(n) time and space; preserve which positions hold lowercase letters versus special characters."""
    letters = []
    special = []
    for character in s:
        if 'a' <= character <= 'z':
            letters.append(character)
        else:
            special.append(character)
    result = []
    for character in s:
        if 'a' <= character <= 'z':
            result.append(letters.pop())
        else:
            result.append(special.pop())
    return ''.join(result)


class Solution:
    def reverseByType(self, s: str) -> str:
        return solve(s)
