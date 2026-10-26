"""3127. Make a Square with the Same Color (Easy).

Specification: https://leetcode.com/problems/make-a-square-with-the-same-color/description/
"""


def solve(grid: list[list[str]]) -> bool:
    """O(1) time and space for a 3-by-3 grid; do not modify its cells."""
    for row in range(2):
        for column in range(2):
            black = 0
            for row_offset in range(2):
                for column_offset in range(2):
                    if grid[row + row_offset][column + column_offset] == 'B':
                        black += 1
            if black != 2:
                return True
    return False


class Solution:
    def canMakeSquare(self, grid: list[list[str]]) -> bool:
        return solve(grid)
