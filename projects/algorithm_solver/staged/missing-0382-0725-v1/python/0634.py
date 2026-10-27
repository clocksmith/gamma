"""634. Find the Derangement of An Array. Use D(n)=(n-1)*(D(n-1)+D(n-2)); only two states are retained."""

def solve(n: int) -> int:
    modulus = 1_000_000_007
    previous, current = 1, 0
    if n == 0:
        return previous
    for length in range(2, n + 1):
        previous, current = current, (length - 1) * (current + previous) % modulus
    return current


class Solution:
    def findDerangement(self, n: int) -> int:
        return solve(n)
