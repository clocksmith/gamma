"""1281. Subtract the Product and Sum of Digits of an Integer (Easy).

Specification: https://leetcode.com/problems/subtract-the-product-and-sum-of-digits-of-an-integer/description/
"""


def solve(n: int) -> int:
    product = 1
    total = 0
    value = n
    while value > 0:
        digit = value % 10
        product *= digit
        total += digit
        value //= 10
    return product - total


class Solution:
    def subtractProductAndSum(self, n: int) -> int:
        return solve(n)
