"""Hack2Hire 6965d17bd0c1ba0f117959a2 (Best Meeting Date by Country) over an INFERRED spec; qualification unknown."""


def solve(participants):
    counts = {}
    for _, country, dates in participants:
        per = counts.setdefault(country, {})
        for d in set(dates):
            per[d] = per.get(d, 0) + 1
    chosen = {}
    for country, per in counts.items():
        best = None
        for d, c in per.items():
            if best is None or c > best[0] or (c == best[0] and d < best[1]):
                best = (c, d)
        if best is not None:
            chosen[country] = best[1]
    attendees = {country: [] for country in chosen}
    for name, country, dates in participants:
        if country in chosen and chosen[country] in dates:
            attendees[country].append(name)
    return [[country, chosen[country], attendees[country]] for country in sorted(chosen)]


class Solution:
    def scheduleMeetings(self, participants):
        return solve(participants)
