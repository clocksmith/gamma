"""2951. Find the Peaks (Easy).

Specification: https://leetcode.com/problems/find-the-peaks/description/
"""


def solve(mountain: list[int]) -> list[int]:
    """O(n) time, O(n) result space; return ascending indices and preserve mountain."""
    peaks = []
    for index in range(1, len(mountain) - 1):
        if mountain[index] > mountain[index - 1] and mountain[index] > mountain[index + 1]:
            peaks.append(index)
    return peaks


class Solution:
    def findPeaks(self, mountain: list[int]) -> list[int]:
        return solve(mountain)
