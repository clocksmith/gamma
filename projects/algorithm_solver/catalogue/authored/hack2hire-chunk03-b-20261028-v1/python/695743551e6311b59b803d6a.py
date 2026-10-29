"""Hack2Hire 695743551e6311b59b803d6a (Neighborhood Party Interval Aggregator, level 1) over an INFERRED spec; qualification unknown."""


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
        intervals = sorted(by_hood[hood])
        start, end = intervals[0]
        for s, e in intervals[1:]:
            if s <= end:
                if e > end: end = e
            else:
                result.append([hood, str(start), str(end)])
                start, end = s, e
        result.append([hood, str(start), str(end)])
    return result


class Solution:
    def aggregatePartyWindows(self, partyWindows, geoDataList):
        return solve(partyWindows, geoDataList)
