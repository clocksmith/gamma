"""3858. Minimum Bitwise OR From Grid."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> int:
    """O(B mn) time and O(1) auxiliary space, B=17; greedily clear bits while preserving one allowed choice per row."""
    answer = (1 << 17) - 1
    for bit in range(16, -1, -1):
        candidate = answer ^ (1 << bit)
        if all(any((value | candidate) == candidate for value in row) for row in grid):
            answer = candidate
    return answer


class Solution:
    def minimumOR(self, grid: list[list[int]]) -> int:
        return solve(grid)
