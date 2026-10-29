"""Hack2Hire 6a08df61bd4165b6d480ff97 (Camera Motion Detection, variant 1) over an INFERRED spec; qualification unknown."""


def solve(times, intensities, threshold):
    result, start = [], None
    for i, value in enumerate(intensities):
        if value >= threshold:
            if start is None:
                start = times[i]
            if i + 1 == len(intensities) or intensities[i + 1] < threshold:
                result.append([start, times[i]])
                start = None
    return result


class Solution:
    def motionPeriods(self, times, intensities, threshold):
        return solve(times, intensities, threshold)
