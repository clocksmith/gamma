"""3894. Traffic Signal Color (Easy).

Specification: https://leetcode.com/problems/traffic-signal-color/description/
"""


def solve(timer: int) -> str:
    """O(1) time and space; use the specified discrete timer conditions, not a periodic cycle."""
    if timer == 0:
        return 'Green'
    if timer == 30:
        return 'Orange'
    if 30 < timer <= 90:
        return 'Red'
    return 'Invalid'


class Solution:
    def trafficSignal(self, timer: int) -> str:
        return solve(timer)
