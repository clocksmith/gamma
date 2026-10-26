"""796. Rotate String (Easy).

Specification: https://leetcode.com/problems/rotate-string/description/
"""


def solve(s: str, goal: str) -> bool:
    """O(n^2) worst-case time, O(n) space; equal-length rotations occur in the doubled string."""
    return len(s) == len(goal) and goal in s + s


class Solution:
    def rotateString(self, s: str, goal: str) -> bool:
        return solve(s, goal)
