"""2413. Smallest Even Multiple (Easy).

Specification: https://leetcode.com/problems/smallest-even-multiple/description/
"""


def solve(n: int) -> int:
    """O(1) time and space; compute lcm(n, 2) for positive n."""
    return n if n % 2 == 0 else 2 * n


class Solution:
    def smallestEvenMultiple(self, n: int) -> int:
        return solve(n)
