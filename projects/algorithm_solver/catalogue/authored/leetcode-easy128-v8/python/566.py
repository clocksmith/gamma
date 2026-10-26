"""566. Reshape the Matrix (Easy).

Specification: https://leetcode.com/problems/reshape-the-matrix/description/
"""


def solve(mat: list[list[int]], r: int, c: int) -> list[list[int]]:
    """O(m * n) time and space; row-major reshape, returning fresh rows even when unchanged."""
    rows, columns = len(mat), len(mat[0])
    if rows * columns != r * c:
        return [row.copy() for row in mat]
    result = [[0] * c for _ in range(r)]
    for index in range(rows * columns):
        result[index // c][index % c] = mat[index // columns][index % columns]
    return result


class Solution:
    def matrixReshape(self, mat: list[list[int]], r: int, c: int) -> list[list[int]]:
        return solve(mat, r, c)
