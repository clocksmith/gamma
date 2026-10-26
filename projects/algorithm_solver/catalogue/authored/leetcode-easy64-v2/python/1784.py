"""1784. Check if Binary String Has at Most One Segment of Ones (Easy).

Specification: https://leetcode.com/problems/check-if-binary-string-has-at-most-one-segment-of-ones/description/
"""


def solve(s: str) -> bool:
    """O(n) time, O(1) space; the problem guarantees s starts with 1."""
    return '01' not in s


class Solution:
    def checkOnesSegment(self, s: str) -> bool:
        return solve(s)
