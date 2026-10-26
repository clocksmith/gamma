"""3218. Minimum Cost for Cutting Cake I: take the most expensive remaining cut before it spans more pieces."""


def solve(m: int, n: int, horizontalCut: list[int], verticalCut: list[int]) -> int:
    """O(m log m + n log n) time and O(m + n) auxiliary space; inputs are read-only."""
    horizontal = sorted(horizontalCut, reverse=True)
    vertical = sorted(verticalCut, reverse=True)
    row_pieces = column_pieces = 1
    row = column = total = 0
    while row < len(horizontal) or column < len(vertical):
        if column == len(vertical) or (row < len(horizontal) and horizontal[row] >= vertical[column]):
            total += horizontal[row] * column_pieces
            row_pieces += 1
            row += 1
        else:
            total += vertical[column] * row_pieces
            column_pieces += 1
            column += 1
    return total


class Solution:
    def minimumCost(self, m: int, n: int, horizontalCut: list[int], verticalCut: list[int]) -> int:
        return solve(m, n, horizontalCut, verticalCut)
