"""Hack2Hire 696336dcf731aa3969ef52a7 (Maximum Concurrent Calls) over an INFERRED spec; qualification unknown."""

DAY = 86400000


def solve(calls):
    events = {}
    for customer, _, start, end in calls:
        bucket = events.setdefault(customer, [])
        bucket.append((start, 1))
        bucket.append((end, -1))
    out = []
    for customer in sorted(events):
        peak = {}
        active, previous = 0, None
        for time, delta in sorted(events[customer]):  # -1 sorts before +1 at the same instant (end exclusive)
            if active and time > previous:
                for day in range(previous // DAY, (time - 1) // DAY + 1):
                    if peak.get(day, 0) < active:
                        peak[day] = active
            active += delta
            previous = time
        out.extend([customer, day, peak[day]] for day in sorted(peak))
    return out


class Solution:
    def maxConcurrentCallsPerDay(self, calls):
        return solve(calls)
