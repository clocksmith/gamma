"""1529. Bulb Switcher IV (Medium).

Specification: https://leetcode.com/problems/bulb-switcher-iv/description/
"""


def solve(target: str) -> int:
    flips = 0
    current = '0'
    for ch in target:
        if ch != current:
            flips += 1
            current = ch
    return flips


class Solution:
    def minFlips(self, target: str) -> int:
        return solve(target)
