"""Hack2Hire 69f3a12f42791c82ab992d99 (User Flight Location Tracker) over an INFERRED spec; qualification unknown."""

from bisect import bisect_right


def solve(flights, userId, time):
    legs = sorted((f[1], f[3], f[0], f[2]) for f in flights if f[4] == userId)
    if not legs:
        return ''
    i = bisect_right([leg[0] for leg in legs], time) - 1
    if i < 0:
        return legs[0][2]
    departure, arrival, origin, destination = legs[i]
    if time == departure:
        return origin
    if time < arrival:
        return ''
    return destination


class Solution:
    def findUserLocation(self, flights, userId, time):
        return solve(flights, userId, time)
