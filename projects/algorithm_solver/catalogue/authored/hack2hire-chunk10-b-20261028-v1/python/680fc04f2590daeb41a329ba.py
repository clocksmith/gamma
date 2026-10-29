"""Hack2Hire 680fc04f2590daeb41a329ba (Find Common Free Days, variant 3 of 3) over an INFERRED spec; qualification unknown."""


def solve(blocks, totalDays, k):
    per = {}
    for person, start, end in blocks:
        per.setdefault(person, []).append((start, end))
    events = []
    for spans in per.values():
        spans.sort()
        cs, ce = spans[0]
        for s, e in spans[1:]:
            if s <= ce + 1:
                ce = max(ce, e)
            else:
                events.append((cs, 1))
                events.append((ce + 1, -1))
                cs, ce = s, e
        events.append((cs, 1))
        events.append((ce + 1, -1))
    events.sort()
    people, busy, i, day, out = len(per), 0, 0, 1, []
    while day <= totalDays:
        while i < len(events) and events[i][0] <= day:
            busy += events[i][1]
            i += 1
        nxt = events[i][0] if i < len(events) else totalDays + 1
        end = min(nxt - 1, totalDays)
        if people - busy >= k:
            if out and out[-1][1] == day - 1:
                out[-1][1] = end
            else:
                out.append([day, end])
        day = end + 1
    return out


class Solution:
    def freeIntervalsForAtLeast(self, blocks, totalDays, k):
        return solve(blocks, totalDays, k)
