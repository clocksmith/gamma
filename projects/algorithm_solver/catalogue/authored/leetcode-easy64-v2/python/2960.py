"""2960. Count Tested Devices After Test Operations (Easy).

Specification: https://leetcode.com/problems/count-tested-devices-after-test-operations/description/
"""


def solve(batteryPercentages: list[int]) -> int:
    """O(n) time, O(1) space; prior successful tests account for all decrements."""
    tested = 0
    for percentage in batteryPercentages:
        if percentage > tested:
            tested += 1
    return tested


class Solution:
    def countTestedDevices(self, batteryPercentages: list[int]) -> int:
        return solve(batteryPercentages)
