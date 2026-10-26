"""2450. Number of Distinct Binary Strings After Applying Operations: count the independent fixed-width flip vectors."""


def solve(s: str, k: int) -> int:
    """O(log(n + 1)) modular arithmetic operations and O(1) auxiliary space; inputs are read-only."""
    # Each starting position contributes a distinct leftmost nonzero coordinate.
    return pow(2, len(s) - k + 1, 1_000_000_007)


class Solution:
    def countDistinctStrings(self, s: str, k: int) -> int:
        return solve(s, k)
