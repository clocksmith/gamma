"""1217. Minimum Cost to Move Chips to The Same Position (Easy).

Specification: https://leetcode.com/problems/minimum-cost-to-move-chips-to-the-same-position/description/
"""


def solve(position: list[int]) -> int:
    """O(n) time, O(1) space; preserve position."""
    odd_count = 0
    for value in position:
        odd_count += value % 2
    return min(odd_count, len(position) - odd_count)


class Solution:
    def minCostToMoveChips(self, position: list[int]) -> int:
        return solve(position)
