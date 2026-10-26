"""3605. Minimum Stability Factor of Array.

Binary-search the longest allowed gcd-stable window and greedily replace the right endpoint of each uncovered bad window; O(n log n) gcd calls and O(n log n) space. Inputs are preserved.
"""

from array import array
from math import gcd


def solve(nums: list[int], maxC: int) -> int:
    n = len(nums)
    logs = [0] * (n + 1)
    for length in range(2, n + 1):
        logs[length] = logs[length // 2] + 1
    table = [array('i', nums)]
    width = 2
    while width <= n:
        half = width // 2
        previous = table[-1]
        table.append(array('i', (gcd(previous[index], previous[index + half]) for index in range(n - width + 1))))
        width *= 2

    def possible(length):
        window = length + 1
        if window > n:
            return True
        level = logs[window]
        span = 1 << level
        start = changes = 0
        while start + window <= n:
            if gcd(table[level][start], table[level][start + window - span]) > 1:
                changes += 1
                if changes > maxC:
                    return False
                start += window
            else:
                start += 1
        return True

    lower, upper = 0, n
    while lower < upper:
        middle = (lower + upper) // 2
        if possible(middle):
            upper = middle
        else:
            lower = middle + 1
    return lower


class Solution:
    def minStable(self, nums: list[int], maxC: int) -> int:
        return solve(nums, maxC)
