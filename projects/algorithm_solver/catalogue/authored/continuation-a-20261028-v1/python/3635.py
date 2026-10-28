def solve(landStartTime, landDuration, waterStartTime, waterDuration):
    first_land = min(start + duration for start, duration in zip(landStartTime, landDuration))
    first_water = min(start + duration for start, duration in zip(waterStartTime, waterDuration))
    land_then_water = min(max(first_land, start) + duration for start, duration in zip(waterStartTime, waterDuration))
    water_then_land = min(max(first_water, start) + duration for start, duration in zip(landStartTime, landDuration))
    return min(land_then_water, water_then_land)


class Solution:
    def earliestFinishTime(self, landStartTime, landDuration, waterStartTime, waterDuration):
        return solve(landStartTime, landDuration, waterStartTime, waterDuration)
