"""409. Longest Palindrome (Easy).

Specification: https://leetcode.com/problems/longest-palindrome/description/
"""


def solve(s: str) -> int:
    """O(n) expected time, O(a) space; pair equal case-sensitive letters and allow one center."""
    counts = {}
    for character in s:
        counts[character] = counts.get(character, 0) + 1
    length = 0
    has_odd = False
    for count in counts.values():
        length += count - count % 2
        if count % 2:
            has_odd = True
    return length + int(has_odd)


class Solution:
    def longestPalindrome(self, s: str) -> int:
        return solve(s)
