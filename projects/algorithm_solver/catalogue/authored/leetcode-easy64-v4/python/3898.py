"""3898. Find the Degree of Each Vertex (Easy).

Specification: https://leetcode.com/problems/find-the-degree-of-each-vertex/description/
"""


def solve(matrix: list[list[int]]) -> list[int]:
    """O(n squared) time, O(n) output space; preserve the adjacency matrix and all rows."""
    result = []
    for row in matrix:
        degree = 0
        for value in row:
            degree += value
        result.append(degree)
    return result


class Solution:
    def findDegrees(self, matrix: list[list[int]]) -> list[int]:
        return solve(matrix)
