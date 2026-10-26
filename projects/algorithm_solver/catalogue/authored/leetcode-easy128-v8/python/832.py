"""832. Flipping an Image (Easy).

Specification: https://leetcode.com/problems/flipping-an-image/description/
"""


def solve(image: list[list[int]]) -> list[list[int]]:
    """O(n^2) time and space; reverse each binary row and invert into fresh rows."""
    return [[1 - value for value in reversed(row)] for row in image]


class Solution:
    def flipAndInvertImage(self, image: list[list[int]]) -> list[list[int]]:
        return solve(image)
