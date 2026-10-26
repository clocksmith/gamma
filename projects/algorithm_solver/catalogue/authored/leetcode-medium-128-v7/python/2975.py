"""2975. Maximum Square Area by Removing Fences From a Field: intersect attainable horizontal and vertical distances and square the largest exactly."""


def solve(m: int, n: int, hFences: list[int], vFences: list[int]) -> int:
    """O(h * h + v * v) expected time and O(h * h + v) auxiliary space; inputs are read-only."""
    horizontal = [1, m, *hFences]
    vertical = [1, n, *vFences]
    distances = set()
    for right in range(len(horizontal)):
        for left in range(right):
            distances.add(abs(horizontal[right] - horizontal[left]))
    best = 0
    for right in range(len(vertical)):
        for left in range(right):
            distance = abs(vertical[right] - vertical[left])
            if distance in distances:
                best = max(best, distance)
    return best * best % 1_000_000_007 if best else -1


class Solution:
    def maximizeSquareArea(self, m: int, n: int, hFences: list[int], vFences: list[int]) -> int:
        return solve(m, n, hFences, vFences)
