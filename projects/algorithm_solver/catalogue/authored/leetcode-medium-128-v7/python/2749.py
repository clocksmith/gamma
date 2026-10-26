"""2749. Minimum Operations to Make the Integer Zero: find the first operation count whose remaining value is a sum of that many powers of two."""


def solve(num1: int, num2: int) -> int:
    """O(60 * 60) bounded bit operations and O(1) auxiliary space on the stated domain; inputs are read-only."""
    for operations in range(1, 61):
        remaining = num1 - operations * num2
        if remaining >= operations and remaining.bit_count() <= operations:
            return operations
    return -1


class Solution:
    def makeTheIntegerZero(self, num1: int, num2: int) -> int:
        return solve(num1, num2)
