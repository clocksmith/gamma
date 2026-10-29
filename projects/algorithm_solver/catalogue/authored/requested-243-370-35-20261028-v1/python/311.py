"""Original frontend 311 variant; qualification unknown."""


def solve(mat1, mat2):
    m, k, n = len(mat1), len(mat1[0]), len(mat2[0])
    res = [[0] * n for _ in range(m)]
    for i in range(m):
        for p in range(k):
            v1 = mat1[i][p]
            if v1 != 0:
                for j in range(n):
                    if mat2[p][j] != 0:
                        res[i][j] += v1 * mat2[p][j]
    return res


multiply = solve


class Solution:
    def multiply(self, mat1, mat2):
        return solve(mat1, mat2)
