"""172. Factorial Trailing Zeroes."""
def solve(n: int) -> int:
    total = 0
    while n:
        n //= 5
        total += n
    return total

class Solution:
    def trailingZeroes(self, n: int) -> int:
        return solve(n)
