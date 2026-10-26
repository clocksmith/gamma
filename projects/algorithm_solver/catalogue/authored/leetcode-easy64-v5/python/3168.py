"""3168. Minimum Number of Chairs in a Waiting Room (Easy).

Specification: https://leetcode.com/problems/minimum-number-of-chairs-in-a-waiting-room/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) auxiliary space; the entry/exit sequence is valid."""
    occupied = 0
    maximum = 0
    for event in s:
        occupied += 1 if event == 'E' else -1
        maximum = max(maximum, occupied)
    return maximum


class Solution:
    def minimumChairs(self, s: str) -> int:
        return solve(s)
