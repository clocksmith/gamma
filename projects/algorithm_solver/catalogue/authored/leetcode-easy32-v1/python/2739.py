"""2739. Total Distance Traveled (Easy).

Specification: https://leetcode.com/problems/total-distance-traveled/description/
"""


def solve(mainTank: int, additionalTank: int) -> int:
    """O(1) time and space; transfers consume a net four main-tank liters."""
    transfers = min(additionalTank, (mainTank - 1) // 4)
    return 10 * (mainTank + transfers)


class Solution:
    def distanceTraveled(self, mainTank: int, additionalTank: int) -> int:
        return solve(mainTank, additionalTank)
