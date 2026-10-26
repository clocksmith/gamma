"""2716. Minimize String Length (Easy).

Specification: https://leetcode.com/problems/minimize-string-length/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space for the lowercase English alphabet."""
    return len(set(s))


class Solution:
    def minimizedStringLength(self, s: str) -> int:
        return solve(s)
