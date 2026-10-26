"""3274. Check if Two Chessboard Squares Have the Same Color (Easy).

Specification: https://leetcode.com/problems/check-if-two-chessboard-squares-have-the-same-color/description/
"""


def solve(coordinate1: str, coordinate2: str) -> bool:
    """O(1) time and space; both coordinates are valid two-character chessboard squares."""
    first = ord(coordinate1[0]) + ord(coordinate1[1])
    second = ord(coordinate2[0]) + ord(coordinate2[1])
    return first % 2 == second % 2


class Solution:
    def checkTwoChessboards(self, coordinate1: str, coordinate2: str) -> bool:
        return solve(coordinate1, coordinate2)
