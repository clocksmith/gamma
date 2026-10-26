"""3800. Minimum Cost to Make Two Binary Strings Equal."""
from __future__ import annotations


def solve(s: str, t: str, flipCost: int, swapCost: int, crossCost: int) -> int:
    """O(n) time and O(1) space; resolve opposite mismatches before equal-direction pairs."""
    forward = backward = 0
    for first, second in zip(s, t):
        if first != second:
            if first == '0':
                forward += 1
            else:
                backward += 1
    opposite = min(forward, backward)
    remaining = abs(forward - backward)
    return opposite * min(swapCost, 2 * flipCost) + (remaining // 2) * min(crossCost + swapCost, 2 * flipCost) + (remaining % 2) * flipCost


class Solution:
    def minimumCost(self, s: str, t: str, flipCost: int, swapCost: int, crossCost: int) -> int:
        return solve(s, t, flipCost, swapCost, crossCost)
