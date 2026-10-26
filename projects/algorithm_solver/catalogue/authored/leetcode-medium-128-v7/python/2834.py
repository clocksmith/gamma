"""2834. Find the Minimum Possible Sum of a Beautiful Array: sum the allowed lower half and the remaining consecutive values starting at target."""


def solve(n: int, target: int) -> int:
    """O(1) arithmetic operations and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    modulus = 1_000_000_007
    small = min(n, target // 2)
    remaining = n - small
    total = small * (small + 1) // 2 + remaining * (2 * target + remaining - 1) // 2
    return total % modulus


class Solution:
    def minimumPossibleSum(self, n: int, target: int) -> int:
        return solve(n, target)
