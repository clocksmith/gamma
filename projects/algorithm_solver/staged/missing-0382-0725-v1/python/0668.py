"""668. Kth Smallest Number in Multiplication Table."""

def solve(m: int, n: int, k: int) -> int:
    if m > n:
        m, n = n, m
    low, high = 1, m * n
    while low < high:
        middle = (low + high) // 2
        count = sum(min(n, middle // row) for row in range(1, m + 1))
        if count >= k:
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def findKthNumber(self, m: int, n: int, k: int) -> int:
        return solve(m, n, k)
