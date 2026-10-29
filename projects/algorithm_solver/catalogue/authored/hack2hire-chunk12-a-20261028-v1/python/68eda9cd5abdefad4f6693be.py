"""Hack2Hire 68eda9cd5abdefad4f6693be (Maximum Interval Overlap Count) over an INFERRED spec; qualification unknown."""


def solve(intervals):
    starts = sorted(iv[0] for iv in intervals)
    ends = sorted(iv[1] for iv in intervals)
    i = j = current = best = 0
    while i < len(starts):
        if starts[i] <= ends[j]:  # closed intervals: a start at an end's coordinate still overlaps
            current += 1
            i += 1
            if current > best:
                best = current
        else:
            current -= 1
            j += 1
    return best


class Solution:
    def maxOverlap(self, intervals):
        return solve(intervals)
