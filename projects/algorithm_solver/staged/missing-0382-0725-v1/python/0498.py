"""498. Diagonal Traverse."""

def solve(mat: list[list[int]]) -> list[int]:
    rows, cols = len(mat), len(mat[0])
    answer = []
    for diagonal in range(rows + cols - 1):
        first = max(0, diagonal - cols + 1)
        last = min(rows - 1, diagonal)
        order = range(last, first - 1, -1) if diagonal % 2 == 0 else range(first, last + 1)
        for row in order:
            answer.append(mat[row][diagonal - row])
    return answer


class Solution:
    def findDiagonalOrder(self, mat: list[list[int]]) -> list[int]:
        return solve(mat)
