"""2651. Calculate Delayed Arrival Time (Easy).

Specification: https://leetcode.com/problems/calculate-delayed-arrival-time/description/
"""


def solve(arrivalTime: int, delayedTime: int) -> int:
    """O(1) time and space; wrap the delayed hour into the 24-hour clock."""
    return (arrivalTime + delayedTime) % 24


class Solution:
    def findDelayedArrivalTime(self, arrivalTime: int, delayedTime: int) -> int:
        return solve(arrivalTime, delayedTime)
