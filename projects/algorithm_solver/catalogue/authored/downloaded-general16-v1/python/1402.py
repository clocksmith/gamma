"""1402. Reducing Dishes (Hard).

Specification: https://leetcode.com/problems/reducing-dishes/description/
"""


def solve(satisfaction):
    running = 0
    total = 0
    for value in sorted(satisfaction, reverse=True):
        running += value
        if running > 0:
            total += running
        else:
            break
    return total


class Solution:
    def maxSatisfaction(self, satisfaction):
        return solve(satisfaction)
