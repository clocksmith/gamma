"""Hack2Hire 6a08e02abd4165b6d480ffa1 (Camera Motion Detection, variant 2) over an INFERRED spec; qualification unknown."""


def _periods(times, intensities, threshold):
    result, start = [], None
    for i, value in enumerate(intensities):
        if value >= threshold:
            if start is None:
                start = times[i]
            if i + 1 == len(intensities) or intensities[i + 1] < threshold:
                result.append((start, times[i]))
                start = None
    return result


def solve(timesA, intensitiesA, timesB, intensitiesB, threshold):
    first, second = _periods(timesA, intensitiesA, threshold), _periods(timesB, intensitiesB, threshold)
    i = j = 0
    result = []
    while i < len(first) and j < len(second):
        low = max(first[i][0], second[j][0])
        high = min(first[i][1], second[j][1])
        if low <= high:
            result.append([low, high])
        if first[i][1] < second[j][1]:
            i += 1
        else:
            j += 1
    return result


class Solution:
    def overlappingMotion(self, timesA, intensitiesA, timesB, intensitiesB, threshold):
        return solve(timesA, intensitiesA, timesB, intensitiesB, threshold)
