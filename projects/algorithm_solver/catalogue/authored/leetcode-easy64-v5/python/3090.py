"""3090. Maximum Length Substring With Two Occurrences (Easy).

Specification: https://leetcode.com/problems/maximum-length-substring-with-two-occurrences/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) alphabet space; maintain at most two copies of each letter."""
    counts = [0] * 26
    left = 0
    longest = 0
    for right, character in enumerate(s):
        added = ord(character) - ord('a')
        counts[added] += 1
        while counts[added] > 2:
            counts[ord(s[left]) - ord('a')] -= 1
            left += 1
        longest = max(longest, right - left + 1)
    return longest


class Solution:
    def maximumLengthSubstring(self, s: str) -> int:
        return solve(s)
