"""1686. Stone Game VI (Medium).

Specification: https://leetcode.com/problems/stone-game-vi/description/
"""


def solve(aliceValues: list[int], bobValues: list[int]) -> int:
    order = sorted(range(len(aliceValues)), key=lambda i: -(aliceValues[i] + bobValues[i]))
    alice = 0
    bob = 0
    for turn, index in enumerate(order):
        if turn % 2 == 0:
            alice += aliceValues[index]
        else:
            bob += bobValues[index]
    if alice > bob:
        return 1
    if alice < bob:
        return -1
    return 0


class Solution:
    def stoneGameVI(self, aliceValues: list[int], bobValues: list[int]) -> int:
        return solve(aliceValues, bobValues)
