"""2332. The Latest Time to Catch a Bus: simulate boarding on sorted copies and move the final feasible arrival off occupied times."""


def solve(buses: list[int], passengers: list[int], capacity: int) -> int:
    """O(b log b + p log p) time and O(b + p) auxiliary space; inputs are read-only."""
    departures = sorted(buses)
    arrivals = sorted(passengers)
    index = boarded = 0
    for departure in departures:
        boarded = 0
        while index < len(arrivals) and arrivals[index] <= departure and boarded < capacity:
            index += 1
            boarded += 1
    candidate = departures[-1] if boarded < capacity else arrivals[index - 1]
    occupied = set(arrivals)
    while candidate in occupied:
        candidate -= 1
    return candidate


class Solution:
    def latestTimeCatchTheBus(self, buses: list[int], passengers: list[int], capacity: int) -> int:
        return solve(buses, passengers, capacity)
