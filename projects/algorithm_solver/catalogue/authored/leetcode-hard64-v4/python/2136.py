"""2136. Earliest Possible Day of Full Bloom."""


def solve(plantTime: list[int], growTime: list[int]) -> int:
    """Plant in nonincreasing growth-time order; O(n log n) time and O(n) space. Inputs are preserved."""
    planted = 0
    answer = 0
    for growth, duration in sorted(zip(growTime, plantTime), reverse=True):
        planted += duration
        answer = max(answer, planted + growth)
    return answer


class Solution:
    def earliestFullBloom(self, plantTime: list[int], growTime: list[int]) -> int:
        return solve(plantTime, growTime)
