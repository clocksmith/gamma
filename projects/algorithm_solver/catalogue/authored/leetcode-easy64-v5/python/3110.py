"""3110. Score of a String (Easy).

Specification: https://leetcode.com/problems/score-of-a-string/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) auxiliary space; the input alphabet is lowercase English."""
    score = 0
    for index in range(1, len(s)):
        score += abs(ord(s[index]) - ord(s[index - 1]))
    return score


class Solution:
    def scoreOfString(self, s: str) -> int:
        return solve(s)
