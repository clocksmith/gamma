"""1550. Three Consecutive Odds (Easy).

Specification: https://leetcode.com/problems/three-consecutive-odds/description/
"""


def solve(arr: list[int]) -> bool:
    """O(n) time, O(1) space; preserve arr."""
    consecutive = 0
    for value in arr:
        consecutive = consecutive + 1 if value % 2 != 0 else 0
        if consecutive == 3:
            return True
    return False


class Solution:
    def threeConsecutiveOdds(self, arr: list[int]) -> bool:
        return solve(arr)
