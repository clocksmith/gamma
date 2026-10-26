"""2187. Minimum Time to Complete Trips: binary search elapsed time and stop counting once the requested trips are reached."""


def solve(time: list[int], totalTrips: int) -> int:
    """O(n * log(T + 1)) time and O(1) auxiliary space for T = min(time) * totalTrips; inputs are read-only."""
    low, high = 1, min(time) * totalTrips
    while low < high:
        middle = (low + high) // 2
        completed = 0
        for duration in time:
            completed += middle // duration
            if completed >= totalTrips:
                break
        if completed >= totalTrips:
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def minimumTime(self, time: list[int], totalTrips: int) -> int:
        return solve(time, totalTrips)
