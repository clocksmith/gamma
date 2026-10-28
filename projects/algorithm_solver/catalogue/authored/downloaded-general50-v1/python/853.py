"""853. Car Fleet (Medium).

Specification: https://leetcode.com/problems/car-fleet/description/
"""


def solve(target: int, position: list[int], speed: list[int]) -> int:
    cars = sorted(zip(position, speed), key=lambda x: -x[0])
    fleets = 0
    slowest = -1.0
    for p, s in cars:
        time = (target - p) / s
        if time > slowest:
            fleets += 1
            slowest = time
    return fleets


class Solution:
    def carFleet(self, target: int, position: list[int], speed: list[int]) -> int:
        return solve(target, position, speed)
