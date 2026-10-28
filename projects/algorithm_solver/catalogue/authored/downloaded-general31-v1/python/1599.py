"""1599. Maximum Profit of Operating a Centennial Wheel (Medium).

Specification: https://leetcode.com/problems/maximum-profit-of-operating-a-centennial-wheel/description/
"""


def solve(customers: list[int], boardingCost: int, runningCost: int) -> int:
    waiting = 0
    profit = 0
    best_profit = 0
    best_rotation = -1
    rotation = 0
    while waiting > 0 or rotation < len(customers):
        if rotation < len(customers):
            waiting += customers[rotation]
        boarded = min(4, waiting)
        waiting -= boarded
        profit += boarded * boardingCost - runningCost
        rotation += 1
        if profit > best_profit:
            best_profit = profit
            best_rotation = rotation
    return best_rotation


class Solution:
    def minOperationsMaxProfit(self, customers: list[int], boardingCost: int, runningCost: int) -> int:
        return solve(customers, boardingCost, runningCost)
