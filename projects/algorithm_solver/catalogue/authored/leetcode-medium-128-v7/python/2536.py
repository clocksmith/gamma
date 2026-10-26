"""2536. Increment Submatrices by One: record rectangle corners in a two-dimensional difference array."""


def solve(n: int, queries: list[list[int]]) -> list[list[int]]:
    """O(n * n + q) time and O(n * n) auxiliary space; inputs are read-only."""
    changes = [[0] * (n + 1) for _ in range(n + 1)]
    for top, left, bottom, right in queries:
        changes[top][left] += 1
        changes[top][right + 1] -= 1
        changes[bottom + 1][left] -= 1
        changes[bottom + 1][right + 1] += 1
    result = [[0] * n for _ in range(n)]
    for row in range(n):
        running = 0
        for column in range(n):
            running += changes[row][column]
            result[row][column] = running + (result[row - 1][column] if row else 0)
    return result


class Solution:
    def rangeAddQueries(self, n: int, queries: list[list[int]]) -> list[list[int]]:
        return solve(n, queries)
