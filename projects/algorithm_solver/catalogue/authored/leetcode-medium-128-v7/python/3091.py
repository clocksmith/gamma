"""3091. Apply Operations to Make Sum of Array Greater Than or Equal to k: balance increments of one value against the number of copies needed to reach k."""
from math import isqrt


def solve(k: int) -> int:
    """O(sqrt(k)) time and O(1) auxiliary space; inputs are read-only."""
    best = k - 1
    for value in range(1, isqrt(k) + 2):
        copies = (k + value - 1) // value
        best = min(best, value + copies - 2)
    return best


class Solution:
    def minOperations(self, k: int) -> int:
        return solve(k)
