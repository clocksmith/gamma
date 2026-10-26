"""1710. Maximum Units on a Truck (Easy).

Specification: https://leetcode.com/problems/maximum-units-on-a-truck/description/
"""


def solve(boxTypes: list[list[int]], truckSize: int) -> int:
    """O(n log n) time, O(n) space; load the highest units per box first using a sorted copy."""
    ordered = sorted(boxTypes, key=lambda box: -box[1])
    remaining = truckSize
    total = 0
    for count, units in ordered:
        loaded = min(count, remaining)
        total += loaded * units
        remaining -= loaded
        if remaining == 0:
            break
    return total


class Solution:
    def maximumUnits(self, boxTypes: list[list[int]], truckSize: int) -> int:
        return solve(boxTypes, truckSize)
