"""1763. Longest Nice Substring (Easy).

Specification: https://leetcode.com/problems/longest-nice-substring/description/
"""


def _is_nice(text):
    seen = set(text)
    for ch in text:
        if ch.lower() not in seen or ch.upper() not in seen:
            return False
    return True


def solve(s: str) -> str:
    for length in range(len(s), 0, -1):
        for start in range(len(s) - length + 1):
            part = s[start:start + length]
            if _is_nice(part):
                return part
    return ''


class Solution:
    def longestNiceSubstring(self, s: str) -> str:
        return solve(s)
