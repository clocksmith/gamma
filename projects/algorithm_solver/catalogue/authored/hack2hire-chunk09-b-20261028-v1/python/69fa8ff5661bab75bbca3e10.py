"""Hack2Hire 69fa8ff5661bab75bbca3e10 (Count Dropped Requests) over an INFERRED spec; qualification unknown."""


def solve(requestTime):
    dropped = 0
    for i, t in enumerate(requestTime):
        if ((i >= 3 and requestTime[i - 3] == t) or (i >= 20 and t - requestTime[i - 20] < 10)
                or (i >= 60 and t - requestTime[i - 60] < 60)):
            dropped += 1
    return dropped


class Solution:
    def droppedRequests(self, requestTime):
        return solve(requestTime)
