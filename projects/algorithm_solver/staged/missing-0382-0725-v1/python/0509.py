"""509. Fibonacci Number."""

def solve(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


class Solution:
    def fib(self, n: int) -> int:
        return solve(n)
