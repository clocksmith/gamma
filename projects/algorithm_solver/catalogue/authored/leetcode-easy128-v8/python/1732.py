"""1732. Find the Highest Altitude (Easy).

Specification: https://leetcode.com/problems/find-the-highest-altitude/description/
"""


def solve(gain: list[int]) -> int:
    """O(n) time, O(1) space; include the initial altitude of zero among prefix sums."""
    altitude = highest = 0
    for change in gain:
        altitude += change
        highest = max(highest, altitude)
    return highest


class Solution:
    def largestAltitude(self, gain: list[int]) -> int:
        return solve(gain)
