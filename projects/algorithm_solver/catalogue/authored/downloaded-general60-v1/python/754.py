"""754. Reach a Number (Medium).

Specification: https://leetcode.com/problems/reach-a-number/description/
"""


def solve(target: int) -> int:
    goal = abs(target)
    steps = 0
    total = 0
    while total < goal or (total - goal) % 2 != 0:
        steps += 1
        total += steps
    return steps


class Solution:
    def reachNumber(self, target: int) -> int:
        return solve(target)
