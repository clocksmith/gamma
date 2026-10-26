"""1383. Maximum Performance of a Team: descending efficiency and a speed heap; O(n log n + n log k) time, O(n) space; exact products."""

from heapq import heappop, heappush


def solve(n: int, speed: list[int], efficiency: list[int], k: int) -> int:
    engineers = sorted(zip(efficiency, speed), reverse=True)
    heap = []
    total_speed = answer = 0
    for minimum_efficiency, candidate_speed in engineers:
        heappush(heap, candidate_speed)
        total_speed += candidate_speed
        if len(heap) > k:
            total_speed -= heappop(heap)
        answer = max(answer, total_speed * minimum_efficiency)
    return answer % 1_000_000_007


class Solution:
    def maxPerformance(self, n: int, speed: list[int], efficiency: list[int], k: int) -> int:
        return solve(n, speed, efficiency, k)
