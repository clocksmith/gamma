"""397. Integer Replacement. Greedily clear low bits; avoid signed 32-bit overflow in JavaScript."""

def solve(n: int) -> int:
    steps = 0
    while n > 1:
        if n % 2 == 0:
            n //= 2
        elif n == 3 or n % 4 == 1:
            n -= 1
        else:
            n += 1
        steps += 1
    return steps


class Solution:
    def integerReplacement(self, n: int) -> int:
        return solve(n)
