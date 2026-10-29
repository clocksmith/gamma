"""Hack2Hire 69cae7e2ff3ebde766ceda54 (Route Nearest Checkpoint) over an INFERRED spec; qualification unknown."""

from bisect import bisect_right
from math import isqrt


def solve(coordinates, distances):
    lengths = []
    prefix = [0]
    for a, b in zip(coordinates, coordinates[1:]):
        length = isqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)
        lengths.append(length)
        prefix.append(prefix[-1] + length)
    total = prefix[-1]
    out = []
    for d in distances:
        if d >= total:
            a = b = coordinates[-1]
            length, r = 1, 0
        else:
            k = bisect_right(prefix, d) - 1
            a, b = coordinates[k], coordinates[k + 1]
            length, r = lengths[k], d - prefix[k]
        best, best_index = -1, 0
        for index, w in enumerate(coordinates):
            dx = length * (a[0] - w[0]) + r * (b[0] - a[0])
            dy = length * (a[1] - w[1]) + r * (b[1] - a[1])
            q = dx * dx + dy * dy
            if best < 0 or q < best:
                best, best_index = q, index
        out.append(best_index)
    return out


class Solution:
    def nearestCheckpoints(self, coordinates, distances):
        return solve(coordinates, distances)
