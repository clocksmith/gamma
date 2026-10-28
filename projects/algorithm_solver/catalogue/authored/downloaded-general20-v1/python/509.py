"""509. Fibonacci Number (Easy).

Specification: https://leetcode.com/problems/fibonacci-number/description/
"""


def solve(n: int) -> int:
    if n < 2:
        return n
    previous = 0
    current = 1
    for _step in range(2, n + 1):
        previous, current = current, previous + current
    return current


class Solution:
    def fib(self, n: int) -> int:
        return solve(n)
