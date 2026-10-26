"""2022. Convert 1D Array Into 2D Array (Easy).

Specification: https://leetcode.com/problems/convert-1d-array-into-2d-array/description/
"""


def solve(original: list[int], m: int, n: int) -> list[list[int]]:
    """O(m * n) time and result space when dimensions match; preserve original and allocate fresh rows."""
    if len(original) != m * n:
        return []
    result = []
    for row in range(m):
        result.append(original[row * n:(row + 1) * n])
    return result


class Solution:
    def construct2DArray(self, original: list[int], m: int, n: int) -> list[list[int]]:
        return solve(original, m, n)
