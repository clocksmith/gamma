"""3856. Trim Trailing Vowels (Easy).

Specification: https://leetcode.com/problems/trim-trailing-vowels/description/
"""


def solve(s: str) -> str:
    """O(n) time and output space; remove only the trailing lowercase vowels."""
    end = len(s)
    while end > 0 and s[end - 1] in 'aeiou':
        end -= 1
    return s[:end]


class Solution:
    def trimTrailingVowels(self, s: str) -> str:
        return solve(s)
