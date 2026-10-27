"""343. Integer Break."""
def solve(n: int) -> int:
    if n <= 3:
        return n - 1
    quotient, remainder = divmod(n, 3)
    if remainder == 0:
        return 3 ** quotient
    if remainder == 1:
        return 3 ** (quotient - 1) * 4
    return 3 ** quotient * 2

class Solution:
    def integerBreak(self, n: int) -> int:
        return solve(n)
