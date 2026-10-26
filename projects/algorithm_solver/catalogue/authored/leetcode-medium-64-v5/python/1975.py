"""1975. Maximum Matrix Sum: preserve negative parity while placing any unavoidable negative sign on the smallest magnitude."""


def solve(matrix: list[list[int]]) -> int:
    """O(n^2) time and O(1) auxiliary space; inputs are read-only."""
    total = negatives = 0
    smallest = abs(matrix[0][0])
    for row in matrix:
        for value in row:
            magnitude = abs(value)
            total += magnitude
            smallest = min(smallest, magnitude)
            negatives += value < 0
    return total - 2 * smallest if negatives % 2 else total


class Solution:
    def maxMatrixSum(self, matrix: list[list[int]]) -> int:
        return solve(matrix)
