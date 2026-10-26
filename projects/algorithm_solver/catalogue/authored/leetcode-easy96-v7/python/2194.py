"""2194. Cells in a Range on an Excel Sheet (Easy).

Specification: https://leetcode.com/problems/cells-in-a-range-on-an-excel-sheet/description/
"""


def solve(s: str) -> list[str]:
    """O(c * r) time and result space; single-letter columns and single-digit rows; column-major order."""
    result = []
    for column in range(ord(s[0]), ord(s[3]) + 1):
        for row in range(int(s[1]), int(s[4]) + 1):
            result.append(chr(column) + str(row))
    return result


class Solution:
    def cellsInRange(self, s: str) -> list[str]:
        return solve(s)
