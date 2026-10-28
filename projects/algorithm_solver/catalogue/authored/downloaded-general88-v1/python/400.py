"""400. Nth Digit (Medium).

Specification: https://leetcode.com/problems/nth-digit/description/
"""


def solve(n: int) -> int:
    digits = 1
    count = 9
    start = 1
    while n > digits * count:
        n -= digits * count
        digits += 1
        count *= 10
        start *= 10
    number = start + (n - 1) // digits
    index = (n - 1) % digits
    return int(str(number)[index])


class Solution:
    def findNthDigit(self, n: int) -> int:
        return solve(n)
