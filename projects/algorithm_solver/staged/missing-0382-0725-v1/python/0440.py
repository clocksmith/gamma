"""440. K-th Smallest in Lexicographical Order."""

def solve(n: int, k: int) -> int:
    current = 1
    k -= 1
    while k:
        first, following, count = current, current + 1, 0
        while first <= n:
            count += min(n + 1, following) - first
            first *= 10
            following *= 10
        if count <= k:
            current += 1
            k -= count
        else:
            current *= 10
            k -= 1
    return current


class Solution:
    def findKthNumber(self, n: int, k: int) -> int:
        return solve(n, k)
