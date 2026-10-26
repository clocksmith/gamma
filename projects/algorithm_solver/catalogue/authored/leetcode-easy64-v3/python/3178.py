"""3178. Find the Child Who Has the Ball After K Seconds (Easy).

Specification: https://leetcode.com/problems/find-the-child-who-has-the-ball-after-k-seconds/description/
"""


def solve(n: int, k: int) -> int:
    """O(1) time and space; reflect the position over a period of 2 * (n - 1)."""
    distance = n - 1
    phase = k % (2 * distance)
    return phase if phase <= distance else 2 * distance - phase


class Solution:
    def numberOfChild(self, n: int, k: int) -> int:
        return solve(n, k)
