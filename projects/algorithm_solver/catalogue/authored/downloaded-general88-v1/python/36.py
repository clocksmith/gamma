"""36. Valid Sudoku (Medium).

Specification: https://leetcode.com/problems/valid-sudoku/description/
"""


def solve(board: list[list[str]]) -> bool:
    seen = set()
    for r in range(9):
        for c in range(9):
            value = board[r][c]
            if value == '.':
                continue
            row_key = f"r{r}-{value}"
            col_key = f"c{c}-{value}"
            box_key = f"b{r // 3}-{c // 3}-{value}"
            if row_key in seen or col_key in seen or box_key in seen:
                return False
            seen.add(row_key)
            seen.add(col_key)
            seen.add(box_key)
    return True


class Solution:
    def isValidSudoku(self, board: list[list[str]]) -> bool:
        return solve(board)
