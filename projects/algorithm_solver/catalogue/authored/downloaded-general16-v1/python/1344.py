"""1344. Angle Between Hands of a Clock (Easy).

Specification: https://leetcode.com/problems/angle-between-hands-of-a-clock/description/
"""


def solve(hour, minutes):
    hour_angle = 30 * (hour % 12) + 0.5 * minutes
    minute_angle = 6 * minutes
    diff = abs(hour_angle - minute_angle)
    return min(diff, 360 - diff)


class Solution:
    def angleClock(self, hour, minutes):
        return solve(hour, minutes)
