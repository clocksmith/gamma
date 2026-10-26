"""3345. Smallest Divisible Digit Product I (Easy).

Specification: https://leetcode.com/problems/smallest-divisible-digit-product-i/description/
"""


def solve(n: int, t: int) -> int:
    """O(log n) time, O(1) space; at most ten candidates reach a multiple of ten."""
    candidate = n
    while True:
        remaining = candidate
        product = 1
        while remaining > 0:
            product *= remaining % 10
            remaining //= 10
        if product % t == 0:
            return candidate
        candidate += 1


class Solution:
    def smallestNumber(self, n: int, t: int) -> int:
        return solve(n, t)
