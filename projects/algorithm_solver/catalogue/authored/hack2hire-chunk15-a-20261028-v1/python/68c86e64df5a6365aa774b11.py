"""Hack2Hire 68c86e64df5a6365aa774b11 (Campground Carpool) over an INFERRED spec; qualification unknown."""


CAMP = 'Campground'


def arrival_times(nxt, start):
    times = {start: 0}
    current, now = start, 0
    while current != CAMP:
        current, duration = nxt[current]
        now += duration
        times[current] = now
    return times


def solve(roads, friends, start1, start2):
    nxt = {}
    for source, target, duration in roads:
        nxt[source] = (target, duration)
    first, second = arrival_times(nxt, start1), arrival_times(nxt, start2)
    sides = ([], [])
    for index, (name, home) in enumerate(friends):
        a, b = first.get(home), second.get(home)
        if b is None or (a is not None and a <= b):
            sides[0].append((a, index, name))
        else:
            sides[1].append((b, index, name))
    return [[item[2] for item in sorted(side)] for side in sides]


class Solution:
    def assignFriends(self, roads, friends, start1, start2):
        return solve(roads, friends, start1, start2)
