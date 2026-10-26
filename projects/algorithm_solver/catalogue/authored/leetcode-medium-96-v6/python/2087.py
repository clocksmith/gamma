"""2087. Minimum Cost Homecoming of a Robot in a Grid: pay once for each required row and column entered on a monotone path."""


def solve(startPos: list[int], homePos: list[int], rowCosts: list[int], colCosts: list[int]) -> int:
    """O(abs(dr) + abs(dc)) time and O(1) auxiliary space; inputs are read-only."""
    row, column = startPos
    answer = 0
    row_step = 1 if homePos[0] > row else -1
    while row != homePos[0]:
        row += row_step
        answer += rowCosts[row]
    column_step = 1 if homePos[1] > column else -1
    while column != homePos[1]:
        column += column_step
        answer += colCosts[column]
    return answer


class Solution:
    def minCost(self, startPos: list[int], homePos: list[int], rowCosts: list[int], colCosts: list[int]) -> int:
        return solve(startPos, homePos, rowCosts, colCosts)
