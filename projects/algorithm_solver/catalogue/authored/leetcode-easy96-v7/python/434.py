"""434. Number of Segments in a String (Easy).

Specification: https://leetcode.com/problems/number-of-segments-in-a-string/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; segments are maximal non-space runs."""
    count = 0
    for index, character in enumerate(s):
        if character != ' ' and (index == 0 or s[index - 1] == ' '):
            count += 1
    return count


class Solution:
    def countSegments(self, s: str) -> int:
        return solve(s)
