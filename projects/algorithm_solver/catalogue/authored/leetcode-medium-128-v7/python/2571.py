"""2571. Minimum Operations to Reduce an Integer to 0: collapse runs of set bits using signed powers of two."""


def solve(n: int) -> int:
    """O(log(n + 1)) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    value = n
    operations = 0
    while value:
        if value & 1:
            operations += 1
            value += 1 if value & 3 == 3 else -1
        else:
            value >>= 1
    return operations


class Solution:
    def minOperations(self, n: int) -> int:
        return solve(n)
