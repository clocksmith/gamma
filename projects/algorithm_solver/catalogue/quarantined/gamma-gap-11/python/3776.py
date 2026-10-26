"""3776. Minimum Moves to Balance Circular Array."""
from __future__ import annotations


def solve(balance: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; consume nearest supplies for the sole possible deficit."""
    if sum(balance) < 0:
        return -1
    negative = next((index for index, value in enumerate(balance) if value < 0), -1)
    if negative < 0:
        return 0
    remaining = -balance[negative]
    answer = 0
    n = len(balance)
    for distance in range(1, n // 2 + 1):
        left = (negative - distance) % n
        right = (negative + distance) % n
        supply = balance[left] + (balance[right] if right != left else 0)
        taken = min(remaining, supply)
        answer += distance * taken
        remaining -= taken
        if remaining == 0:
            return answer
    return -1


class Solution:
    def minMoves(self, balance: list[int]) -> int:
        return solve(balance)
