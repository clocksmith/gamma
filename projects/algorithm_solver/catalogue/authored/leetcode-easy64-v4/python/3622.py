"""3622. Check Divisibility by Digit Sum and Product (Easy).

Specification: https://leetcode.com/problems/check-divisibility-by-digit-sum-and-product/description/
"""


def solve(n: int) -> bool:
    """O(d) time, O(1) space; d is the decimal digit count."""
    remaining = n
    digitSum = 0
    digitProduct = 1
    while remaining > 0:
        digit = remaining % 10
        digitSum += digit
        digitProduct *= digit
        remaining //= 10
    return n % (digitSum + digitProduct) == 0


class Solution:
    def checkDivisibility(self, n: int) -> bool:
        return solve(n)
