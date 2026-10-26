"""1337. The K Weakest Rows in a Matrix (Easy).

Specification: https://leetcode.com/problems/the-k-weakest-rows-in-a-matrix/description/
"""


def solve(mat: list[list[int]], k: int) -> list[int]:
    """O(rows * columns + rows log rows) time, O(rows) space; preserve mat."""
    ranked = []
    for row, cells in enumerate(mat):
        soldiers = sum(cells)
        ranked.append((soldiers, row))
    ranked.sort()
    return [ranked[index][1] for index in range(k)]


class Solution:
    def kWeakestRows(self, mat: list[list[int]], k: int) -> list[int]:
        return solve(mat, k)
