"""4056. Number of Intersecting Interval Pairs I.

Specification: https://leetcode.com/problems/number-of-intersecting-interval-pairs-i/description/
"""

from __future__ import annotations


def solve(intervals: list[list[int]]) -> int:
    """O(n^2) time and O(1) auxiliary space; closed endpoints count as intersection. Inputs are preserved."""
    return sum(max(intervals[first][0], intervals[second][0]) <= min(intervals[first][1], intervals[second][1])
               for first in range(len(intervals)) for second in range(first + 1, len(intervals)))
