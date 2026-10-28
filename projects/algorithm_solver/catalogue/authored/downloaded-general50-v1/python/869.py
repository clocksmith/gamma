"""869. Reordered Power of 2 (Medium).

Specification: https://leetcode.com/problems/reordered-power-of-2/description/
"""


def _signature(x):
    return "".join(sorted(str(x)))


def solve(n: int) -> bool:
    target = _signature(n)
    power = 1
    while power <= 1000000000:
        if _signature(power) == target:
            return True
        power *= 2
    return False


class Solution:
    def reorderedPowerOf2(self, n: int) -> bool:
        return solve(n)
