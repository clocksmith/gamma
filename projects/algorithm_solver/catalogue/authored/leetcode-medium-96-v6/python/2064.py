"""2064. Minimized Maximum of Products Distributed to Any Store: binary search the smallest store limit that needs no more than n stores."""


def solve(n: int, quantities: list[int]) -> int:
    """O(m log M) time and O(1) auxiliary space for m types and maximum quantity M; inputs are read-only."""
    low, high = 1, max(quantities)
    while low < high:
        middle = (low + high) // 2
        needed = 0
        for quantity in quantities:
            needed += (quantity + middle - 1) // middle
            if needed > n:
                break
        if needed <= n:
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def minimizedMaximum(self, n: int, quantities: list[int]) -> int:
        return solve(n, quantities)
