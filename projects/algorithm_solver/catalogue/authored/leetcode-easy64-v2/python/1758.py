"""1758. Minimum Changes To Make Alternating Binary String (Easy).

Specification: https://leetcode.com/problems/minimum-changes-to-make-alternating-binary-string/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; compare the two complementary alternating patterns."""
    mismatches = 0
    for index, character in enumerate(s):
        expected = '0' if index % 2 == 0 else '1'
        if character != expected:
            mismatches += 1
    return min(mismatches, len(s) - mismatches)


class Solution:
    def minOperations(self, s: str) -> int:
        return solve(s)
