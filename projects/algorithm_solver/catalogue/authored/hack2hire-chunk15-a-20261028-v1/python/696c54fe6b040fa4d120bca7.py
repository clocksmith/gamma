"""Hack2Hire 696c54fe6b040fa4d120bca7 (Datapoint Window Sum by Tag, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(datapoints, tag, k):
    times, values = [], []
    for point in datapoints:
        if tag in point['tags']:
            times.append(point['timestamp'])
            values.append(point['value'])
    result, left, total = [], 0, 0
    for i in range(len(times)):
        total += values[i]
        while times[left] < times[i] - k + 1:
            total -= values[left]
            left += 1
        result.append(total)
    return result


class Solution:
    def windowSums(self, datapoints, tag, k):
        return solve(datapoints, tag, k)
