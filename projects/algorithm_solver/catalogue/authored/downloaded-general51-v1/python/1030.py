"""1030. Matrix Cells in Distance Order (Easy).

Specification: https://leetcode.com/problems/matrix-cells-in-distance-order/description/
"""


def solve(rows: int, cols: int, rCenter: int, cCenter: int) -> list[list[int]]:
    cells = [[r, c] for r in range(rows) for c in range(cols)]
    cells.sort(key=lambda cell: (abs(cell[0] - rCenter) + abs(cell[1] - cCenter), cell[0], cell[1]))
    return cells


class Solution:
    def allCellsDistOrder(self, rows: int, cols: int, rCenter: int, cCenter: int) -> list[list[int]]:
        return solve(rows, cols, rCenter, cCenter)
