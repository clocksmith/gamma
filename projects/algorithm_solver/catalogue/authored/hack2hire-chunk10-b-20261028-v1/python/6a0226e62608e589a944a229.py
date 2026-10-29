"""Hack2Hire 6a0226e62608e589a944a229 (Fill Layover With Experiences) over an INFERRED spec; qualification unknown."""


def solve(durations, totalHours):
    options = sorted(set(durations))
    unreachable = totalHours + 1
    best = [0] + [unreachable] * totalHours
    for s in range(1, totalHours + 1):
        b = unreachable
        for d in options:
            if d > s:
                break
            c = best[s - d] + 1
            if c < b:
                b = c
        best[s] = b
    return best[totalHours] if best[totalHours] <= totalHours else -1


class Solution:
    def minBookings(self, durations, totalHours):
        return solve(durations, totalHours)
