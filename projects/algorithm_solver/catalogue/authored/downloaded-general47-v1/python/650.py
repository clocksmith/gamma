"""650. 2 Keys Keyboard (Medium).

Specification: https://leetcode.com/problems/2-keys-keyboard/description/
"""


def solve(n: int) -> int:
    steps = 0
    value = n
    divisor = 2
    while value > 1:
        while value % divisor == 0:
            steps += divisor
            value //= divisor
        divisor += 1
    return steps


class Solution:
    def minSteps(self, n: int) -> int:
        return solve(n)
