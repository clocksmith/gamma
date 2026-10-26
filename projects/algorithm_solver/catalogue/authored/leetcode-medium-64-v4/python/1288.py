"""1288. Remove Covered Intervals: sort starts increasingly and equal-start ends decreasingly."""


def solve(intervals: list[list[int]]) -> int:
    """O(n log(n + 1)) time and O(n) auxiliary space; inputs are read-only."""
    farthest = -1
    retained = 0
    for start, end in sorted(intervals, key=lambda interval: (interval[0], -interval[1])):
        if end > farthest:
            farthest = end
            retained += 1
    return retained


class Solution:
    def removeCoveredIntervals(self, intervals: list[list[int]]) -> int:
        return solve(intervals)
