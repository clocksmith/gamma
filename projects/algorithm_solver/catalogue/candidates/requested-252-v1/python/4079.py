"""4079. Prime Subset Selection I.

Specification: https://leetcode.com/problems/prime-subset-selection-i/description/
"""

from __future__ import annotations


def solve(n: int, s: int) -> list[int]:
    """O(n log log n) time and O(n) space; the smallest-prime prefix maximizes cardinality. Inputs are preserved."""
    composite = bytearray(n + 1)
    prime = 2
    while prime * prime <= n:
        if not composite[prime]:
            for multiple in range(prime * prime, n + 1, prime):
                composite[multiple] = 1
        prime += 1
    answer = []
    total = 0
    for prime in range(2, n + 1):
        if composite[prime]:
            continue
        if total + prime > s:
            break
        answer.append(prime)
        total += prime
    return answer
