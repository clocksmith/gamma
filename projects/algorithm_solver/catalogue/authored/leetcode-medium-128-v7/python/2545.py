"""2545. Sort the Students by Their Kth Score: sort independently copied rows by descending kth score."""


def solve(score: list[list[int]], k: int) -> list[list[int]]:
    """O(r log r + r * c) time and O(r * c) auxiliary space; inputs are read-only."""
    return [row[:] for row in sorted(score, key=lambda row: row[k], reverse=True)]


class Solution:
    def sortTheStudents(self, score: list[list[int]], k: int) -> list[list[int]]:
        return solve(score, k)
