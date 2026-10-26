"""1802. Maximum Value at a Given Index in a Bounded Array: binary search the peak using exact arithmetic-series costs for both sides."""


def solve(n: int, index: int, maxSum: int) -> int:
    """O(log(maxSum + 1)) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    def side_sum(length: int, height: int) -> int:
        descending = min(length, height - 1)
        return descending * (2 * height - descending - 1) // 2 + length - descending

    low, high = 1, maxSum
    while low < high:
        middle = (low + high + 1) // 2
        needed = middle + side_sum(index, middle) + side_sum(n - index - 1, middle)
        if needed <= maxSum:
            low = middle
        else:
            high = middle - 1
    return low


class Solution:
    def maxValue(self, n: int, index: int, maxSum: int) -> int:
        return solve(n, index, maxSum)
