"""3007. Maximum Number That Sum of the Prices Is Less Than or Equal to K: binary search cumulative selected-bit counts using exact integers."""


def solve(k: int, x: int) -> int:
    """O(log^2(k + 2)) bounded integer operations and O(1) auxiliary variables; inputs are read-only."""
    def price(limit):
        count = limit + 1
        bit = 1 << (x - 1)
        total = 0
        while bit <= limit:
            cycle = bit * 2
            total += (count // cycle) * bit + max(0, count % cycle - bit)
            if total > k:
                return total
            bit <<= x
        return total

    low = 0
    high = (k + 1) << x
    while low + 1 < high:
        middle = (low + high) // 2
        if price(middle) <= k:
            low = middle
        else:
            high = middle
    return low


class Solution:
    def findMaximumNumber(self, k: int, x: int) -> int:
        return solve(k, x)
