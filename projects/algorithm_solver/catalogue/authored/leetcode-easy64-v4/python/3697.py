"""3697. Compute Decimal Representation (Easy).

Specification: https://leetcode.com/problems/compute-decimal-representation/description/
"""


def solve(n: int) -> list[int]:
    """O(d) time and output space; emit nonzero place values in descending order."""
    result = []
    remaining = n
    place = 1
    while remaining > 0:
        digit = remaining % 10
        if digit != 0:
            result.append(digit * place)
        place *= 10
        remaining //= 10
    result.reverse()
    return result


class Solution:
    def decimalRepresentation(self, n: int) -> list[int]:
        return solve(n)
