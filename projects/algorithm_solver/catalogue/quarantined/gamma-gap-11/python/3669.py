"""3669. Balanced K-Factor Decomposition."""
from __future__ import annotations
from math import isqrt


def solve(n: int, k: int) -> list[int]:
    """O(sqrt(n) + k * D^(k-1)) worst-case time, O(D + k) space; D is the divisor count."""
    divisors = []
    for factor in range(1, isqrt(n) + 1):
        if n % factor == 0:
            divisors.append(factor)
            if factor * factor != n:
                divisors.append(n // factor)
    divisors.sort()
    answer = [1] * (k - 1) + [n]
    best_gap = n - 1
    path = []

    def search(remaining, slots, lower):
        nonlocal answer, best_gap
        if slots == 1:
            if remaining >= lower:
                first = path[0] if path else remaining
                gap = remaining - first
                if gap < best_gap:
                    best_gap = gap
                    answer = path + [remaining]
            return
        for factor in divisors:
            if factor < lower:
                continue
            if factor ** slots > remaining:
                break
            if remaining % factor == 0:
                path.append(factor)
                search(remaining // factor, slots - 1, factor)
                path.pop()

    search(n, k, 1)
    return answer


class Solution:
    def minDifference(self, n: int, k: int) -> list[int]:
        return solve(n, k)
