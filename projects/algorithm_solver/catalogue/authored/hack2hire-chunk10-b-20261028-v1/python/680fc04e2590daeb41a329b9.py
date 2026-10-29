"""Hack2Hire 680fc04e2590daeb41a329b9 (Find Common Free Days, variant 2 of 3) over an INFERRED spec; qualification unknown."""


def solve(blocks, totalDays):
    spans = sorted((start, end) for _, start, end in blocks)
    out, free_from = [], 1  # first day not known to be busy
    for start, end in spans:
        if start > free_from and free_from <= totalDays:
            out.append([free_from, min(start - 1, totalDays)])
        free_from = max(free_from, end + 1)
    if free_from <= totalDays:
        out.append([free_from, totalDays])
    return out


class Solution:
    def commonFreeIntervals(self, blocks, totalDays):
        return solve(blocks, totalDays)
