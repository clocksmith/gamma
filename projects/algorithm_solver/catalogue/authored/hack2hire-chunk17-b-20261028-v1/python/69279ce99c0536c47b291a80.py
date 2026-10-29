"""Hack2Hire 69279ce99c0536c47b291a80 (Find Peak Event Moment) over an INFERRED spec; qualification unknown."""


def solve(intervals):
    starts = sorted(entry for entry, _ in intervals)
    ends = sorted(leave for _, leave in intervals)
    present = 0
    best = 0
    moment = starts[0]
    j = 0
    for s in starts:
        while ends[j] <= s:
            present -= 1
            j += 1
        present += 1
        if present > best:
            best = present
            moment = s
    return moment


class Solution:
    def findPeakMoment(self, intervals):
        return solve(intervals)
