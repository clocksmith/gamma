"""2507. Smallest Value After Replacing With Sum of Prime Factors: repeat prime-factor summation until the value reaches a fixed point."""


def solve(n: int) -> int:
    """O(sqrt(n) * log(n + 1)) time and O(1) auxiliary space; inputs are read-only."""
    value = n
    while True:
        remaining = value
        total = 0
        factor = 2
        while factor * factor <= remaining:
            while remaining % factor == 0:
                total += factor
                remaining //= factor
            factor += 1
        if remaining > 1:
            total += remaining
        if total == value:
            return value
        value = total


class Solution:
    def smallestValue(self, n: int) -> int:
        return solve(n)
