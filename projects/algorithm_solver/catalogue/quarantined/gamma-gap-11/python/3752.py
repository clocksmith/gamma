"""3752. Lexicographically Smallest Negated Permutation that Sums to Target."""
from __future__ import annotations


def solve(n: int, target: int) -> list[int]:
    """O(n) time and O(n) space; greedily include the largest feasible negative magnitude."""
    total = n * (n + 1) // 2
    if abs(target) > total or (total - target) % 2:
        return []
    remaining = (total - target) // 2
    negative = [False] * (n + 1)
    answer = []
    for value in range(n, 0, -1):
        if value <= remaining:
            remaining -= value
            negative[value] = True
            answer.append(-value)
    for value in range(1, n + 1):
        if not negative[value]:
            answer.append(value)
    return answer


class Solution:
    def lexSmallestNegatedPerm(self, n: int, target: int) -> list[int]:
        return solve(n, target)
