"""168. Excel Sheet Column Title (Easy).

Specification: https://leetcode.com/problems/excel-sheet-column-title/description/
"""


def solve(columnNumber: int) -> str:
    result = ''
    value = columnNumber
    while value > 0:
        value -= 1
        result = chr(65 + (value % 26)) + result
        value //= 26
    return result


class Solution:
    def convertToTitle(self, columnNumber: int) -> str:
        return solve(columnNumber)
