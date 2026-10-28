"""498. Diagonal Traverse (Medium).

Specification: https://leetcode.com/problems/diagonal-traverse/description/
"""


def solve(mat: list[list[int]]) -> list[int]:
    rows, cols = len(mat), len(mat[0])
    groups = {}
    for r in range(rows):
        for c in range(cols):
            groups.setdefault(r + c, []).append(mat[r][c])
    result = []
    for key in range(rows + cols - 1):
        group = groups[key]
        if key % 2 == 0:
            group = group[::-1]
        result.extend(group)
    return result


class Solution:
    def findDiagonalOrder(self, mat: list[list[int]]) -> list[int]:
        return solve(mat)
