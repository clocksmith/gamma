"""3765. Complete Prime Number."""
from __future__ import annotations


def solve(num: int) -> bool:
    """O(log(num) * sqrt(num)) time and O(log num) auxiliary space; exact integer divisibility."""
    def prime(value):
        if value < 2:
            return False
        if value % 2 == 0:
            return value == 2
        divisor = 3
        while divisor * divisor <= value:
            if value % divisor == 0:
                return False
            divisor += 2
        return True
    digits = str(num)
    for length in range(1, len(digits) + 1):
        if not prime(int(digits[:length])) or not prime(int(digits[-length:])):
            return False
    return True


class Solution:
    def completePrime(self, num: int) -> bool:
        return solve(num)
