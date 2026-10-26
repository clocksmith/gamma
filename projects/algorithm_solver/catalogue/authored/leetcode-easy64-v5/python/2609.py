"""2609. Find the Longest Balanced Substring of a Binary String (Easy).

Specification: https://leetcode.com/problems/find-the-longest-balanced-substring-of-a-binary-string/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) auxiliary space; preserve s."""
    zeros = 0
    ones = 0
    longest = 0
    for character in s:
        if character == '0':
            if ones > 0:
                zeros = 0
                ones = 0
            zeros += 1
        else:
            ones += 1
            longest = max(longest, 2 * min(zeros, ones))
    return longest


class Solution:
    def findTheLongestBalancedSubstring(self, s: str) -> int:
        return solve(s)
