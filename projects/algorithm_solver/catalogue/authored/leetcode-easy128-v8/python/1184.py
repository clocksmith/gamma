"""1184. Distance Between Bus Stops (Easy).

Specification: https://leetcode.com/problems/distance-between-bus-stops/description/
"""


def solve(distance: list[int], start: int, destination: int) -> int:
    """O(n) time, O(1) space; compare the two complementary arcs of the circular route."""
    first, last = min(start, destination), max(start, destination)
    total = direct = 0
    for index, length in enumerate(distance):
        total += length
        if first <= index < last:
            direct += length
    return min(direct, total - direct)


class Solution:
    def distanceBetweenBusStops(self, distance: list[int], start: int, destination: int) -> int:
        return solve(distance, start, destination)
