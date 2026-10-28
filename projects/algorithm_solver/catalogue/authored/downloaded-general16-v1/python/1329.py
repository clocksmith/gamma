"""1329. Sort the Matrix Diagonally (Medium).

Specification: https://leetcode.com/problems/sort-the-matrix-diagonally/description/
"""


def solve(mat):
    m, n = len(mat), len(mat[0])
    diagonals = {}
    for i in range(m):
        for j in range(n):
            diagonals.setdefault(i - j, []).append(mat[i][j])
    for values in diagonals.values():
        values.sort()
    positions = {}
    answer = [[0] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            key = i - j
            index = positions.get(key, 0)
            positions[key] = index + 1
            answer[i][j] = diagonals[key][index]
    return answer


class Solution:
    def diagonalSort(self, mat):
        return solve(mat)
