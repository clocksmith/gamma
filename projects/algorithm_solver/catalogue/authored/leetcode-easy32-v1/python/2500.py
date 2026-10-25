"""2500. Delete Greatest Value in Each Row (Easy).

Specification: https://leetcode.com/problems/delete-greatest-value-in-each-row/description/
"""


def solve(grid: list[list[int]]) -> int:
    """O(m*n*log n) time, O(m*n) space; sort copies and preserve all inputs."""
    rows = [sorted(row) for row in grid]
    result = 0
    for column in range(len(rows[0])):
        greatest = 0
        for row in rows:
            greatest = max(greatest, row[column])
        result += greatest
    return result


class Solution:
    def deleteGreatestValue(self, grid: list[list[int]]) -> int:
        return solve(grid)
