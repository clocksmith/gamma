"""849. Maximize Distance to Closest Person (Medium).

Specification: https://leetcode.com/problems/maximize-distance-to-closest-person/description/
"""


def solve(seats: list[int]) -> int:
    best = 0
    last = -1
    for i, value in enumerate(seats):
        if value == 1:
            if last == -1:
                best = max(best, i)
            else:
                best = max(best, (i - last) // 2)
            last = i
    best = max(best, len(seats) - 1 - last)
    return best


class Solution:
    def maxDistToClosest(self, seats: list[int]) -> int:
        return solve(seats)
