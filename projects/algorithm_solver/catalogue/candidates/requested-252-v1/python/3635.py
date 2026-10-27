"""3635. Earliest Finish Time for Land and Water Rides II.

Specification: https://leetcode.com/problems/earliest-finish-time-for-land-and-water-rides-ii/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(land count + water count) time, O(1) auxiliary space; evaluate both ride orders.
Inputs are not modified.
"""

def solve(landStartTime, landDuration, waterStartTime, waterDuration):
    land_finished = min(start + duration for start, duration in zip(landStartTime, landDuration))
    water_finished = min(start + duration for start, duration in zip(waterStartTime, waterDuration))
    land_first = min(max(land_finished, start) + duration for start, duration in zip(waterStartTime, waterDuration))
    water_first = min(max(water_finished, start) + duration for start, duration in zip(landStartTime, landDuration))
    return min(land_first, water_first)


class Solution:
    def earliestFinishTime(self, landStartTime, landDuration, waterStartTime, waterDuration):
        return solve(landStartTime, landDuration, waterStartTime, waterDuration)
