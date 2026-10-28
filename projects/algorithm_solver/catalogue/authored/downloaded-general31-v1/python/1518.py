"""1518. Water Bottles (Easy).

Specification: https://leetcode.com/problems/water-bottles/description/
"""


def solve(numBottles: int, numExchange: int) -> int:
    total = numBottles
    empty = numBottles
    while empty >= numExchange:
        exchanged = empty // numExchange
        total += exchanged
        empty = empty % numExchange + exchanged
    return total


class Solution:
    def numWaterBottles(self, numBottles: int, numExchange: int) -> int:
        return solve(numBottles, numExchange)
