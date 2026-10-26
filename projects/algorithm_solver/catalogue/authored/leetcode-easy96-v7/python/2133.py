"""2133. Check if Every Row and Column Contains All Numbers (Easy).

Specification: https://leetcode.com/problems/check-if-every-row-and-column-contains-all-numbers/description/
"""


def solve(matrix: list[list[int]]) -> bool:
    """O(n^2) time, O(n) space; values are in 1..n; preserve matrix and row identities."""
    size = len(matrix)
    for index in range(size):
        row = set()
        column = set()
        for other in range(size):
            row.add(matrix[index][other])
            column.add(matrix[other][index])
        if len(row) != size or len(column) != size:
            return False
    return True


class Solution:
    def checkValid(self, matrix: list[list[int]]) -> bool:
        return solve(matrix)
