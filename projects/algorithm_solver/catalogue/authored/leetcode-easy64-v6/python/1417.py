"""1417. Reformat The String (Easy).

Specification: https://leetcode.com/problems/reformat-the-string/description/
"""


def solve(s: str) -> str:
    """O(n) time and space; alternate ASCII letters and digits, preserving within-type order."""
    first = []
    second = []
    for character in s:
        if '0' <= character <= '9':
            second.append(character)
        else:
            first.append(character)
    if abs(len(first) - len(second)) > 1:
        return ''
    if len(first) < len(second):
        first, second = second, first
    result = []
    for index, character in enumerate(first):
        result.append(character)
        if index < len(second):
            result.append(second[index])
    return ''.join(result)


class Solution:
    def reformat(self, s: str) -> str:
        return solve(s)
