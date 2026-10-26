"""2251. Number of Flowers in Full Bloom."""

from bisect import bisect_left, bisect_right


def solve(flowers: list[list[int]], people: list[int]) -> list[int]:
    """Count starts at or before a visit minus ends strictly before it; O((F+P) log F) time, O(F+P) space. Inputs are preserved."""
    starts = sorted(interval[0] for interval in flowers)
    ends = sorted(interval[1] for interval in flowers)
    return [bisect_right(starts, instant) - bisect_left(ends, instant) for instant in people]


class Solution:
    def fullBloomFlowers(self, flowers: list[list[int]], people: list[int]) -> list[int]:
        return solve(flowers, people)
