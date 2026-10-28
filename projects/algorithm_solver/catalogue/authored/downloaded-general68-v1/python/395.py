"""395. Longest Substring with At Least K Repeating Characters (Medium).

Specification: https://leetcode.com/problems/longest-substring-with-at-least-k-repeating-characters/description/
"""


def _count_in(s, k, start, end):
    if end - start < k:
        return 0
    counts = {}
    for i in range(start, end):
        counts[s[i]] = counts.get(s[i], 0) + 1
    for i in range(start, end):
        if counts[s[i]] < k:
            return max(_count_in(s, k, start, i), _count_in(s, k, i + 1, end))
    return end - start


def solve(s: str, k: int) -> int:
    return _count_in(s, k, 0, len(s))


class Solution:
    def longestSubstring(self, s: str, k: int) -> int:
        return solve(s, k)
