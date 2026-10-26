"""3000. Maximum Area of Longest Diagonal Rectangle (Easy).

Specification: https://leetcode.com/problems/maximum-area-of-longest-diagonal-rectangle/description/
"""


def solve(dimensions: list[list[int]]) -> int:
    """O(n) time, O(1) auxiliary space; compare squared diagonals exactly; preserve inputs."""
    longest_squared = -1
    largest_area = 0
    for length, width in dimensions:
        diagonal_squared = length * length + width * width
        area = length * width
        if diagonal_squared > longest_squared or (diagonal_squared == longest_squared and area > largest_area):
            longest_squared = diagonal_squared
            largest_area = area
    return largest_area


class Solution:
    def areaOfMaxDiagonal(self, dimensions: list[list[int]]) -> int:
        return solve(dimensions)
