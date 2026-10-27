"""365. Water and Jug Problem."""
from math import gcd

def solve(jug1Capacity: int, jug2Capacity: int, targetCapacity: int) -> bool:
    if targetCapacity == 0:
        return True
    if jug1Capacity + jug2Capacity < targetCapacity:
        return False
    return targetCapacity % gcd(jug1Capacity, jug2Capacity) == 0

class Solution:
    def canMeasureWater(self, jug1Capacity, jug2Capacity, targetCapacity):
        return solve(jug1Capacity, jug2Capacity, targetCapacity)
