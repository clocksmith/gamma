"""1663. Smallest String With A Given Numeric Value: place all extra letter value as far to the right as possible."""


def solve(n: int, k: int) -> str:
    """O(n) time and O(n) space including the result; inputs are read-only."""
    letters = ['a'] * n
    remaining = k - n
    for index in range(n - 1, -1, -1):
        extra = min(25, remaining)
        letters[index] = chr(ord('a') + extra)
        remaining -= extra
    return ''.join(letters)


class Solution:
    def getSmallestString(self, n: int, k: int) -> str:
        return solve(n, k)
