"""3726. Remove Zeros in Decimal Representation (Easy).

Specification: https://leetcode.com/problems/remove-zeros-in-decimal-representation/description/
"""


def solve(n: int) -> int:
    """O(d) time, O(1) space; n <= 10^15 stays within exact JavaScript integer range."""
    remaining = n
    result = 0
    place = 1
    while remaining > 0:
        digit = remaining % 10
        if digit != 0:
            result += digit * place
            place *= 10
        remaining //= 10
    return result


class Solution:
    def removeZeros(self, n: int) -> int:
        return solve(n)
