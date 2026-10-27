"""233. Number of Digit One."""
def solve(n: int) -> int:
    total = 0
    factor = 1
    while factor <= n:
        lower = n % factor
        current = (n // factor) % 10
        higher = n // (factor * 10)
        if current == 0:
            total += higher * factor
        elif current == 1:
            total += higher * factor + lower + 1
        else:
            total += (higher + 1) * factor
        factor *= 10
    return total

class Solution:
    def countDigitOne(self, n: int) -> int:
        return solve(n)
