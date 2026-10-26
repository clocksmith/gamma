"""3821. Find Nth Smallest Integer With K One Bits."""
from __future__ import annotations


def solve(n: int, k: int) -> int:
    """O(B^2) time and space, B=50; exact combinatorial unranking without 32-bit truncation."""
    choose = [[0] * 51 for _ in range(51)]
    for row in range(51):
        choose[row][0] = 1
        for column in range(1, row + 1):
            choose[row][column] = choose[row - 1][column - 1] + choose[row - 1][column]
    answer = 0
    needed = k
    rank = n
    for bit in range(49, -1, -1):
        without = choose[bit][needed] if needed <= bit else 0
        if rank > without:
            rank -= without
            answer += 1 << bit
            needed -= 1
    return answer


class Solution:
    def nthSmallest(self, n: int, k: int) -> int:
        return solve(n, k)
