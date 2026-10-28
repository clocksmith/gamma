"""440. K-th Smallest in Lexicographical Order (Hard).

Specification: https://leetcode.com/problems/k-th-smallest-in-lexicographical-order/description/
"""


def _count_steps(n, prefix):
    steps = 0
    first = prefix
    last = prefix + 1
    while first <= n:
        steps += min(last, n + 1) - first
        first *= 10
        last *= 10
    return steps


def solve(n: int, k: int) -> int:
    current = 1
    remaining = k - 1
    while remaining > 0:
        steps = _count_steps(n, current)
        if steps <= remaining:
            current += 1
            remaining -= steps
        else:
            current *= 10
            remaining -= 1
    return current


class Solution:
    def findKthNumber(self, n: int, k: int) -> int:
        return solve(n, k)
