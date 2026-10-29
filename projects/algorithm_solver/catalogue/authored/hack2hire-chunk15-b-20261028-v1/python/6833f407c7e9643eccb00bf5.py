"""Hack2Hire 6833f407c7e9643eccb00bf5 (Find Restaurant Intervals) over an INFERRED spec; qualification unknown."""


def solve(open, close, capacity, reservations, partySize):
    events = []
    for start, end, seats in reservations:
        events.append((start, seats))
        events.append((end, -seats))
    events.sort()
    result = []
    used = 0
    current = open
    begin = None
    i = 0
    while True:
        free = capacity - used >= partySize
        if free and begin is None:
            begin = current
        if not free and begin is not None:
            if current > begin:
                result.append([begin, current])
            begin = None
        if i == len(events):
            break
        t = events[i][0]
        while i < len(events) and events[i][0] == t:
            used += events[i][1]
            i += 1
        current = t
    if begin is not None and close > begin:
        result.append([begin, close])
    merged = []
    for a, b in result:
        if merged and merged[-1][1] == a:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    return merged


class Solution:
    def availableIntervals(self, open, close, capacity, reservations, partySize):
        return solve(open, close, capacity, reservations, partySize)
