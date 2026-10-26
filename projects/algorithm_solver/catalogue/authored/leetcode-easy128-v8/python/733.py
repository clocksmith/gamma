"""733. Flood Fill (Easy).

Specification: https://leetcode.com/problems/flood-fill/description/
"""


def solve(image: list[list[int]], sr: int, sc: int, color: int) -> list[list[int]]:
    """O(m * n) time and space; iterative traversal colors a fresh image and preserves input rows."""
    result = [row.copy() for row in image]
    original = image[sr][sc]
    if original == color:
        return result
    stack = [(sr, sc)]
    result[sr][sc] = color
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
    while stack:
        row, column = stack.pop()
        for row_step, column_step in directions:
            next_row, next_column = row + row_step, column + column_step
            if (0 <= next_row < len(result) and 0 <= next_column < len(result[0])
                    and result[next_row][next_column] == original):
                result[next_row][next_column] = color
                stack.append((next_row, next_column))
    return result


class Solution:
    def floodFill(self, image: list[list[int]], sr: int, sc: int, color: int) -> list[list[int]]:
        return solve(image, sr, sc, color)
