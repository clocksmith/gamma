"""424. Longest Repeating Character Replacement (Medium).

Specification: https://leetcode.com/problems/longest-repeating-character-replacement/description/
"""


def solve(s: str, k: int) -> int:
    counts = {}
    left = 0
    max_count = 0
    best = 0
    for right, ch in enumerate(s):
        counts[ch] = counts.get(ch, 0) + 1
        max_count = max(max_count, counts[ch])
        while right - left + 1 - max_count > k:
            counts[s[left]] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


class Solution:
    def characterReplacement(self, s: str, k: int) -> int:
        return solve(s, k)
