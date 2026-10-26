"""1883. Minimum Skips to Arrive at Meeting On Time.

Use integer distance-units to avoid floating-point rounding; O(n^2) time, O(n) space. Inputs are preserved.
"""

def solve(dist: list[int], speed: int, hoursBefore: int) -> int:
    n = len(dist)
    deadline = speed * hoursBefore
    if sum(dist) > deadline:
        return -1
    times = [0] + [float('inf')] * n
    for road, distance in enumerate(dist):
        following = [float('inf')] * (n + 1)
        for skipped in range(road + 1):
            if times[skipped] == float('inf'):
                continue
            arrival = times[skipped] + distance
            waited = arrival if road == n - 1 else (arrival + speed - 1) // speed * speed
            following[skipped] = min(following[skipped], waited)
            if road != n - 1:
                following[skipped + 1] = min(following[skipped + 1], arrival)
        times = following
    return next((skipped for skipped, time in enumerate(times) if time <= deadline), -1)


class Solution:
    def minSkips(self, dist: list[int], speed: int, hoursBefore: int) -> int:
        return solve(dist, speed, hoursBefore)
