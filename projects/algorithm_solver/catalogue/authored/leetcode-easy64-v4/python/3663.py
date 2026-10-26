"""3663. Find The Least Frequent Digit (Easy).

Specification: https://leetcode.com/problems/find-the-least-frequent-digit/description/
"""


def solve(n: int) -> int:
    """O(d) time, O(1) space; count present digits only and break ties by digit."""
    counts = [0] * 10
    remaining = n
    while remaining > 0:
        counts[remaining % 10] += 1
        remaining //= 10
    result = -1
    smallestCount = float('inf')
    for digit in range(10):
        if 0 < counts[digit] < smallestCount:
            result = digit
            smallestCount = counts[digit]
    return result


class Solution:
    def getLeastFrequentDigit(self, n: int) -> int:
        return solve(n)
