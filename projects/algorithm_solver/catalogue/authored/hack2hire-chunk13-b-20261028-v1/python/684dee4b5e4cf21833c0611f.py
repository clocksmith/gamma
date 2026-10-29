"""Hack2Hire 684dee4b5e4cf21833c0611f (Remove Covered Point) over an INFERRED spec; qualification unknown."""


def solve(intervals, idx):
    out = []
    rest = idx
    done = False
    for start, end in intervals:
        if not done and rest < end - start:
            point = start + rest
            done = True
            if start < point:
                out.append([start, point])
            if point + 1 < end:
                out.append([point + 1, end])
        else:
            if not done:
                rest -= end - start
            out.append([start, end])
    return out


class Solution:
    def removeCoveredPoint(self, intervals, idx):
        return solve(intervals, idx)
