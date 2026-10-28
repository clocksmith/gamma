"""118. Pascal's Triangle (Easy).

Specification: https://leetcode.com/problems/pascals-triangle/description/
"""


def solve(numRows: int) -> list[list[int]]:
    result = []
    for row in range(numRows):
        current = [1] * (row + 1)
        for col in range(1, row):
            current[col] = result[row - 1][col - 1] + result[row - 1][col]
        result.append(current)
    return result


class Solution:
    def generate(self, numRows: int) -> list[list[int]]:
        return solve(numRows)
