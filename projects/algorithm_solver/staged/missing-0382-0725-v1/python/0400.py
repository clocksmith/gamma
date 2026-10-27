"""400. Nth Digit."""

def solve(n: int) -> int:
    digits, first, count = 1, 1, 9
    while n > digits * count:
        n -= digits * count
        digits += 1
        first *= 10
        count *= 10
    number = first + (n - 1) // digits
    return int(str(number)[(n - 1) % digits])


class Solution:
    def findNthDigit(self, n: int) -> int:
        return solve(n)
