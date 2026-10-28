"""52. N-Queens II (Hard).

Specification: https://leetcode.com/problems/n-queens-ii/description/
"""


def solve(n: int) -> int:
    count = 0
    columns = set()
    diagonals = set()
    anti_diagonals = set()

    def backtrack(row):
        nonlocal count
        if row == n:
            count += 1
            return
        for col in range(n):
            if col in columns or (row - col) in diagonals or (row + col) in anti_diagonals:
                continue
            columns.add(col)
            diagonals.add(row - col)
            anti_diagonals.add(row + col)
            backtrack(row + 1)
            columns.remove(col)
            diagonals.remove(row - col)
            anti_diagonals.remove(row + col)

    backtrack(0)
    return count


class Solution:
    def totalNQueens(self, n: int) -> int:
        return solve(n)
