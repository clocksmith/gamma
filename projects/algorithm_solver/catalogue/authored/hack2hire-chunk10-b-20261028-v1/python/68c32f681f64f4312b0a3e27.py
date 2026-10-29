"""Hack2Hire 68c32f681f64f4312b0a3e27 (F1 Last Lap Improvement, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def solve(drivers, lapTimes):
    keyed = []
    for name, laps in zip(drivers, lapTimes):
        last = laps[-1]
        keyed.append((-(sum(laps) - last - last * (len(laps) - 1)), name))
    keyed.sort()
    return [name for _, name in keyed]


class Solution:
    def rankLastLapImprovement(self, drivers, lapTimes):
        return solve(drivers, lapTimes)
