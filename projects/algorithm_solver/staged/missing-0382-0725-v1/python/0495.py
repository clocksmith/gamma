"""495. Teemo Attacking."""

def solve(timeSeries: list[int], duration: int) -> int:
    if not timeSeries:
        return 0
    return duration + sum(min(duration, b - a) for a, b in zip(timeSeries, timeSeries[1:]))


class Solution:
    def findPoisonedDuration(self, timeSeries: list[int], duration: int) -> int:
        return solve(timeSeries, duration)
