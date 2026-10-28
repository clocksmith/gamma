"""1552. Magnetic Force Between Two Balls (Medium).

Specification: https://leetcode.com/problems/magnetic-force-between-two-balls/description/
"""


def _can_place(position, m, distance):
    placed = 1
    last = position[0]
    for i in range(1, len(position)):
        if position[i] - last >= distance:
            placed += 1
            last = position[i]
            if placed >= m:
                return True
    return placed >= m


def solve(position: list[int], m: int) -> int:
    ordered = sorted(position)
    left, right = 1, ordered[-1] - ordered[0]
    best = 1
    while left <= right:
        mid = (left + right) // 2
        if _can_place(ordered, m, mid):
            best = mid
            left = mid + 1
        else:
            right = mid - 1
    return best


class Solution:
    def maxDistance(self, position: list[int], m: int) -> int:
        return solve(position, m)
