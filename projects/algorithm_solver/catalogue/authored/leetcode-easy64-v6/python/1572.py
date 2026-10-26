"""1572. Matrix Diagonal Sum (Easy).

Specification: https://leetcode.com/problems/matrix-diagonal-sum/description/
"""


def solve(mat: list[list[int]]) -> int:
    """O(n) time, O(1) space; count the center once; preserve mat and its rows."""
    size = len(mat)
    result = 0
    for row in range(size):
        result += mat[row][row]
        other_column = size - row - 1
        if other_column != row:
            result += mat[row][other_column]
    return result


class Solution:
    def diagonalSum(self, mat: list[list[int]]) -> int:
        return solve(mat)
