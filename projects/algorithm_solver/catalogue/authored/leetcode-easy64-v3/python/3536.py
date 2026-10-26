"""3536. Maximum Product of Two Digits (Easy).

Specification: https://leetcode.com/problems/maximum-product-of-two-digits/description/
"""


def solve(n: int) -> int:
    """O(log n) time, O(1) space; retain the two largest digit occurrences."""
    largest = 0
    second = 0
    while n > 0:
        digit = n % 10
        if digit >= largest:
            second = largest
            largest = digit
        elif digit > second:
            second = digit
        n //= 10
    return largest * second


class Solution:
    def maxProduct(self, n: int) -> int:
        return solve(n)
