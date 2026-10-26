"""1982. Find Array Given Subset Sums: signed multiset partition using the smallest adjacent difference."""

from collections import Counter


def solve(n: int, sums: list[int]) -> list[int]:
    """O(n * 2^n) time and O(2^n) auxiliary space. Inputs are preserved."""
    remaining = sorted(sums)
    answer = []
    for _ in range(n):
        difference = remaining[1] - remaining[0]
        counts = Counter(remaining)
        lower = []
        upper = []
        for value in remaining:
            if counts[value] == 0:
                continue
            counts[value] -= 1
            counts[value + difference] -= 1
            lower.append(value)
            upper.append(value + difference)
        if 0 in lower:
            answer.append(difference)
            remaining = lower
        else:
            answer.append(-difference)
            remaining = upper
    return answer


class Solution:
    def recoverArray(self, n: int, sums: list[int]) -> list[int]:
        return solve(n, sums)
