"""Refuel retroactively at the largest reachable, unused fuel station."""
from heapq import heappop, heappush


def solve(target: int, startFuel: int, stations: list[list[int]]) -> int:
    """O(n log n) time and O(n) space; all supplied station rows are preserved."""
    available = []
    reachable, next_station, stops = startFuel, 0, 0
    while reachable < target:
        while next_station < len(stations) and stations[next_station][0] <= reachable:
            heappush(available, -stations[next_station][1])
            next_station += 1
        if not available:
            return -1
        reachable -= heappop(available)
        stops += 1
    return stops


class Solution:
    def minRefuelStops(self, target: int, startFuel: int, stations: list[list[int]]) -> int:
        return solve(target, startFuel, stations)
