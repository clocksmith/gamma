"""Hack2Hire 68fd342247bea664c0bba313 (Find Earliest Available Meeting Slot) over an INFERRED spec; qualification unknown."""


def _minute(text):
    return int(text[:2]) * 60 + int(text[3:])


def solve(events, k):
    busy = []
    for event in events:
        _, _, start, end = event.split(' ')
        busy.append((_minute(start), _minute(end)))
    busy.sort()
    free_from = 0  # first minute not covered by any busy interval seen so far
    for start, end in busy:
        if start - free_from >= k:
            return '%02d:%02d' % divmod(free_from, 60)
        free_from = max(free_from, end + 1)
    if 1440 - free_from >= k:
        return '%02d:%02d' % divmod(free_from, 60)
    return '-1'


class Solution:
    def earliestMeetingSlot(self, events, k):
        return solve(events, k)
