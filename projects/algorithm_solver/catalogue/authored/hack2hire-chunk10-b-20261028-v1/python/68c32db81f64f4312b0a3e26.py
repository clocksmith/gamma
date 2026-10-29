"""Hack2Hire 68c32db81f64f4312b0a3e26 (F1 Last Lap Improvement, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(drivers, lapTimes):
    best_key, best_name = None, None
    for name, laps in zip(drivers, lapTimes):
        last = laps[-1]
        key = sum(laps) - last - last * (len(laps) - 1)  # (L - 1) * improvement
        if best_key is None or key > best_key or (key == best_key and name < best_name):
            best_key, best_name = key, name
    return best_name


class Solution:
    def bestLastLapImprovement(self, drivers, lapTimes):
        return solve(drivers, lapTimes)
