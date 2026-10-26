"""171. Excel Sheet Column Number (Easy).

Specification: https://leetcode.com/problems/excel-sheet-column-number/description/
"""


def solve(columnTitle: str) -> int:
    """O(n) time, O(1) auxiliary space; accumulate the bijective base-26 value."""
    result = 0
    for character in columnTitle:
        result = result * 26 + ord(character) - 64
    return result


class Solution:
    def titleToNumber(self, columnTitle: str) -> int:
        return solve(columnTitle)
