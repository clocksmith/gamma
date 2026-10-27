"""352. Data Stream as Disjoint Intervals."""
from bisect import bisect_left

class SummaryRanges:
    def __init__(self):
        self.intervals = []

    def addNum(self, value: int) -> None:
        intervals = self.intervals
        index = bisect_left(intervals, [value, value])
        start = end = value
        if index > 0 and intervals[index - 1][1] + 1 >= value:
            index -= 1
            start = intervals[index][0]
            end = max(end, intervals[index][1])
            intervals.pop(index)
        while index < len(intervals) and intervals[index][0] <= end + 1:
            end = max(end, intervals[index][1])
            intervals.pop(index)
        intervals.insert(index, [start, end])

    def getIntervals(self) -> list[list[int]]:
        return [interval[:] for interval in self.intervals]

def solve(values: list[int]) -> list[list[list[int]]]:
    ranges = SummaryRanges()
    result = []
    for value in values:
        ranges.addNum(value)
        result.append(ranges.getIntervals())
    return result
