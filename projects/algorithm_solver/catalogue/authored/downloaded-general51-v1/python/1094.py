"""1094. Car Pooling (Medium).

Specification: https://leetcode.com/problems/car-pooling/description/
"""


def solve(trips: list[list[int]], capacity: int) -> bool:
    changes = [0] * 1001
    for passengers, frm, to in trips:
        changes[frm] += passengers
        changes[to] -= passengers
    current = 0
    for change in changes:
        current += change
        if current > capacity:
            return False
    return True


class Solution:
    def carPooling(self, trips: list[list[int]], capacity: int) -> bool:
        return solve(trips, capacity)
