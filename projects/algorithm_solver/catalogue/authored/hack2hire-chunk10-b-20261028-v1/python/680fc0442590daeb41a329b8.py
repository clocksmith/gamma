"""Hack2Hire 680fc0442590daeb41a329b8 (Find Common Free Days, variant 1 of 3) over an INFERRED spec; qualification unknown."""


def solve(blocks, totalDays):
    diff = [0] * (totalDays + 2)
    for _, start, end in blocks:
        if start <= totalDays:
            diff[start] += 1
            diff[min(end, totalDays) + 1] -= 1
    out, covered = [], 0
    for day in range(1, totalDays + 1):
        covered += diff[day]
        if covered == 0:
            out.append(day)
    return out


class Solution:
    def commonFreeDays(self, blocks, totalDays):
        return solve(blocks, totalDays)
