"""2397. Maximum Rows Covered by Columns: enumerate the bounded column masks and count contained row masks."""


def solve(matrix: list[list[int]], numSelect: int) -> int:
    """O(mn + (m + n) * 2^n) time and O(m) auxiliary space for n <= 12 columns; inputs are read-only."""
    columns = len(matrix[0])
    masks = []
    for row in matrix:
        mask = 0
        for column, value in enumerate(row):
            if value:
                mask |= 1 << column
        masks.append(mask)
    best = 0
    for selected in range(1 << columns):
        if selected.bit_count() != numSelect:
            continue
        covered = sum((mask & selected) == mask for mask in masks)
        best = max(best, covered)
    return best


class Solution:
    def maximumRows(self, matrix: list[list[int]], numSelect: int) -> int:
        return solve(matrix, numSelect)
