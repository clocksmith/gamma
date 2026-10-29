"""Hack2Hire 69609171bb250997304ac843 (Neighborhood Party Interval Aggregator, level 2) over an INFERRED spec; qualification unknown."""


def group(partyWindows, geoDataList):
    window = {row[0]: (int(row[1]), int(row[2])) for row in partyWindows}
    by_hood = {}
    for party, hood in geoDataList:
        by_hood.setdefault(hood, []).append(window[party])
    return by_hood


def solve(partyWindows, geoDataList):
    by_hood = group(partyWindows, geoDataList)
    result = []
    for hood in sorted(by_hood):
        events = []
        for s, e in by_hood[hood]:
            events.append((s, 1))
            events.append((e, -1))
        events.sort()  # at equal hours the -1 (end) sorts before +1 (start)
        active = peak = 0
        for _, delta in events:
            active += delta
            if active > peak: peak = active
        result.append([hood, peak])
    return result


class Solution:
    def peakConcurrentParties(self, partyWindows, geoDataList):
        return solve(partyWindows, geoDataList)
