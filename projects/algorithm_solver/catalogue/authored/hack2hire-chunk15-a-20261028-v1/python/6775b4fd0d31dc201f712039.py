"""Hack2Hire 6775b4fd0d31dc201f712039 (Count Days for Scheduled Tasks) over an INFERRED spec; qualification unknown."""


def solve(intervals, goal):
    multiplicity = {}
    for interval in intervals:
        multiplicity[interval] = multiplicity.get(interval, 0) + 1
    items = list(multiplicity.items())

    def reaches(day):
        x, total = day - 1, 0
        for interval, count in items:
            total += (x // interval + 1) * count
            if total >= goal:
                return True
        return False

    lo, hi = 1, 1 + (goal - 1) * min(intervals)
    while lo < hi:
        mid = (lo + hi) // 2
        if reaches(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


class Solution:
    def daysToGoal(self, intervals, goal):
        return solve(intervals, goal)
