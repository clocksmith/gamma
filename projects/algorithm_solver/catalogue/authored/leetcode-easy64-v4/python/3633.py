"""3633. Earliest Finish Time for Land and Water Rides I (Easy).

Specification: https://leetcode.com/problems/earliest-finish-time-for-land-and-water-rides-i/description/
"""


def solve(
    landStartTime: list[int],
    landDuration: list[int],
    waterStartTime: list[int],
    waterDuration: list[int],
) -> int:
    """O(n + m) time, O(1) auxiliary space; earliest first completion dominates; preserve inputs."""
    landFinish = min(start + duration for start, duration in zip(landStartTime, landDuration))
    waterFinish = min(start + duration for start, duration in zip(waterStartTime, waterDuration))
    result = float('inf')
    for start, duration in zip(landStartTime, landDuration):
        result = min(result, max(waterFinish, start) + duration)
    for start, duration in zip(waterStartTime, waterDuration):
        result = min(result, max(landFinish, start) + duration)
    return result


class Solution:
    def earliestFinishTime(
        self,
        landStartTime: list[int],
        landDuration: list[int],
        waterStartTime: list[int],
        waterDuration: list[int],
    ) -> int:
        return solve(landStartTime, landDuration, waterStartTime, waterDuration)
