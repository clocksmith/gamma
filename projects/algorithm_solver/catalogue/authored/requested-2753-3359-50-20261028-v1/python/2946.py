"""Original frontend 2946 variant; qualification unknown."""


def solve(mat, k: int) -> bool:
    n = len(mat[0])
    shift = k % n
    if shift == 0:
        return True
    for row in mat:
        for j in range(n):
            if row[j] != row[(j + shift) % n]:
                return False
    return True


areSimilar = solve


class Solution:
    def areSimilar(self, mat, k: int) -> bool:
        return solve(mat, k)
