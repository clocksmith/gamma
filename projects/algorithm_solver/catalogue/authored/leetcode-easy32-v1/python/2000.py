"""2000. Reverse Prefix of Word (Easy).

Specification: https://leetcode.com/problems/reverse-prefix-of-word/description/
"""


def solve(word: str, ch: str) -> str:
    """O(n) time and space; reverse through the first matching character."""
    end = word.find(ch)
    if end == -1:
        return word
    return word[:end + 1][::-1] + word[end + 1:]


class Solution:
    def reversePrefix(self, word: str, ch: str) -> str:
        return solve(word, ch)
