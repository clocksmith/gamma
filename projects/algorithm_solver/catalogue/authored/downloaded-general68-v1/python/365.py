"""365. Water and Jug Problem (Medium).

Specification: https://leetcode.com/problems/water-and-jug-problem/description/
"""


import math


def solve(x: int, y: int, target: int) -> bool:
    if target == 0:
        return True
    if x + y < target:
        return False
    return target % math.gcd(x, y) == 0


class Solution:
    def canMeasureWater(self, x: int, y: int, target: int) -> bool:
        return solve(x, y, target)
