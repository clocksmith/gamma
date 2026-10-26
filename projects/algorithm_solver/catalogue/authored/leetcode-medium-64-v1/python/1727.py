"""1727. Largest Submatrix With Rearrangements: sort a copy of each row histogram while preserving column height identity."""


def solve(matrix: list[list[int]]) -> int:
    """O(rows * columns * log(columns + 1)) time and O(columns) auxiliary space; inputs are read-only."""
    heights = [0] * len(matrix[0])
    answer = 0
    for row in matrix:
        for column, value in enumerate(row):
            heights[column] = heights[column] + 1 if value else 0
        ordered = sorted(heights, reverse=True)
        for width, height in enumerate(ordered, start=1):
            answer = max(answer, width * height)
    return answer


class Solution:
    def largestSubmatrix(self, matrix: list[list[int]]) -> int:
        return solve(matrix)
