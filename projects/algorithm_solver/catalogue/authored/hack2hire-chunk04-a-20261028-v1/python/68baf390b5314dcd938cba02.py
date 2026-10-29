"""Hack2Hire 68baf390b5314dcd938cba02 (Split Stay Booking) over an INFERRED spec; qualification unknown."""


def solve(availability, start, end):
    prefix_end, suffix_start = [], []
    for days in availability:
        present = set(days)
        a = start - 1
        while a < end and a + 1 in present:
            a += 1
        b = end + 1
        while b > start and b - 1 in present:
            b -= 1
        prefix_end.append(a)
        suffix_start.append(b)
    n = len(availability)
    result = [[i] for i in range(n) if prefix_end[i] == end]
    for i in range(n):
        high = min(prefix_end[i], end - 1)
        for j in range(n):
            if i != j and max(start, suffix_start[j] - 1) <= high:
                result.append([i, j])
    return result


class Solution:
    def findSplitStays(self, availability, start, end):
        return solve(availability, start, end)
