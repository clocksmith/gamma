"""1780. Check if Number is a Sum of Powers of Three: reject a ternary representation containing the digit two."""


def solve(n: int) -> bool:
    """O(log(n + 1)) time and O(1) auxiliary space; inputs are read-only."""
    remaining = n
    while remaining:
        if remaining % 3 == 2:
            return False
        remaining //= 3
    return True


class Solution:
    def checkPowersOfThree(self, n: int) -> bool:
        return solve(n)
