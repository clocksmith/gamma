"""495. Teemo Attacking (Easy).

Specification: https://leetcode.com/problems/teemo-attacking/description/
"""


def solve(timeSeries: list[int], duration: int) -> int:
    total = 0
    for i, time in enumerate(timeSeries):
        if i == len(timeSeries) - 1:
            total += duration
        else:
            total += min(duration, timeSeries[i + 1] - time)
    return total


class Solution:
    def findPoisonedDuration(self, timeSeries: list[int], duration: int) -> int:
        return solve(timeSeries, duration)
