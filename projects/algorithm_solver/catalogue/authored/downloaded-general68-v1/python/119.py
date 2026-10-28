"""119. Pascal's Triangle II (Easy).

Specification: https://leetcode.com/problems/pascals-triangle-ii/description/
"""


def solve(rowIndex: int) -> list[int]:
    row = [1]
    for i in range(1, rowIndex + 1):
        nxt = [1] * (i + 1)
        for col in range(1, i):
            nxt[col] = row[col - 1] + row[col]
        row = nxt
    return row


class Solution:
    def getRow(self, rowIndex: int) -> list[int]:
        return solve(rowIndex)
