"""1893. Check if All the Integers in a Range Are Covered (Easy).

Specification: https://leetcode.com/problems/check-if-all-the-integers-in-a-range-are-covered/description/
"""


def solve(ranges: list[list[int]], left: int, right: int) -> bool:
    """O(n + W) time, O(W) space; W = right - left + 1; preserve ranges."""
    width = right - left + 1
    changes = [0] * (width + 1)
    for start, end in ranges:
        first = max(left, start)
        last = min(right, end)
        if first <= last:
            changes[first - left] += 1
            changes[last - left + 1] -= 1
    coverage = 0
    for offset in range(width):
        coverage += changes[offset]
        if coverage == 0:
            return False
    return True


class Solution:
    def isCovered(self, ranges: list[list[int]], left: int, right: int) -> bool:
        return solve(ranges, left, right)
