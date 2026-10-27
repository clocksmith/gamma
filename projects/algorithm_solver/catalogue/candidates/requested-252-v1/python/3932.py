"""3932. Count K-th Roots in a Range.

Specification: https://leetcode.com/problems/count-k-th-roots-in-a-range/description/
"""

from __future__ import annotations


def solve(l: int, r: int, k: int) -> int:
    """O(k log(r+2)) time and O(1) space; exact integer root comparison, including zero. Inputs are preserved."""
    def floor_root(bound):
        if bound < 0:
            return -1
        if k == 1 or bound < 2:
            return bound
        def fits(base):
            product = 1
            for _ in range(k):
                if base and product > bound // base:
                    return False
                product *= base
            return True
        low, high = 0, bound + 1
        while low + 1 < high:
            middle = (low + high) // 2
            if fits(middle):
                low = middle
            else:
                high = middle
        return low
    return floor_root(r) - floor_root(l - 1)
