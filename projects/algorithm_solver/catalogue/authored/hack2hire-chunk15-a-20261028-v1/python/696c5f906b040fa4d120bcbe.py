"""Hack2Hire 696c5f906b040fa4d120bcbe (Datapoint Window Sum by Tag, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def solve(datapoints, tag, k):
    values = [point['value'] for point in datapoints if tag in point['tags']]
    result, total = [], 0
    for i in range(len(values)):
        total += values[i]
        if i >= k:
            total -= values[i - k]
        result.append(total)
    return result


class Solution:
    def lastKSums(self, datapoints, tag, k):
        return solve(datapoints, tag, k)
