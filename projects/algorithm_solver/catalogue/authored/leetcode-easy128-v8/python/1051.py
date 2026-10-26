"""1051. Height Checker (Easy).

Specification: https://leetcode.com/problems/height-checker/description/
"""


def solve(heights: list[int]) -> int:
    """O(n + 100) time, O(100) space; compare the original sequence with counting-sort order."""
    counts = [0] * 101
    for height in heights:
        counts[height] += 1
    expected = 1
    mismatches = 0
    for height in heights:
        while counts[expected] == 0:
            expected += 1
        if height != expected:
            mismatches += 1
        counts[expected] -= 1
    return mismatches


class Solution:
    def heightChecker(self, heights: list[int]) -> int:
        return solve(heights)
