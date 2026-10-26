"""1812. Determine Color of a Chessboard Square (Easy).

Specification: https://leetcode.com/problems/determine-color-of-a-chessboard-square/description/
"""


def solve(coordinates: str) -> bool:
    """O(1) time and space; coordinates range from a1 through h8."""
    column = ord(coordinates[0]) - ord('a')
    row = ord(coordinates[1]) - ord('1')
    return (column + row) % 2 == 1


class Solution:
    def squareIsWhite(self, coordinates: str) -> bool:
        return solve(coordinates)
