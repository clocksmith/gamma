"""661. Image Smoother (Easy).

Specification: https://leetcode.com/problems/image-smoother/description/
"""


def solve(img: list[list[int]]) -> list[list[int]]:
    """O(m * n) time and space; floor each neighborhood average into a fresh matrix."""
    rows, columns = len(img), len(img[0])
    result = [[0] * columns for _ in range(rows)]
    for row in range(rows):
        for column in range(columns):
            total = count = 0
            for near_row in range(max(0, row - 1), min(rows, row + 2)):
                for near_column in range(max(0, column - 1), min(columns, column + 2)):
                    total += img[near_row][near_column]
                    count += 1
            result[row][column] = total // count
    return result


class Solution:
    def imageSmoother(self, img: list[list[int]]) -> list[list[int]]:
        return solve(img)
