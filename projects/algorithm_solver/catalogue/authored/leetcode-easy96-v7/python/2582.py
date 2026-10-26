"""2582. Pass the Pillow (Easy).

Specification: https://leetcode.com/problems/pass-the-pillow/description/
"""


def solve(n: int, time: int) -> int:
    """O(1) time and space; fold the elapsed time into a back-and-forth period of 2(n - 1)."""
    period = 2 * (n - 1)
    position = time % period
    return position + 1 if position < n else period - position + 1


class Solution:
    def passThePillow(self, n: int, time: int) -> int:
        return solve(n, time)
