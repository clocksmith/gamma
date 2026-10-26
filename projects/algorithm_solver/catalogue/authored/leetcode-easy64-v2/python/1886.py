"""1886. Determine Whether Matrix Can Be Obtained By Rotation (Easy).

Specification: https://leetcode.com/problems/determine-whether-matrix-can-be-obtained-by-rotation/description/
"""


def solve(mat: list[list[int]], target: list[list[int]]) -> bool:
    """O(n^2) time, O(1) space; compare rotations without mutating either matrix."""
    size = len(mat)
    unchanged = clockwise = half_turn = counterclockwise = True
    for row in range(size):
        for column in range(size):
            value = target[row][column]
            unchanged = unchanged and mat[row][column] == value
            clockwise = clockwise and mat[size - 1 - column][row] == value
            half_turn = half_turn and mat[size - 1 - row][size - 1 - column] == value
            counterclockwise = counterclockwise and mat[column][size - 1 - row] == value
    return unchanged or clockwise or half_turn or counterclockwise


class Solution:
    def findRotation(self, mat: list[list[int]], target: list[list[int]]) -> bool:
        return solve(mat, target)
