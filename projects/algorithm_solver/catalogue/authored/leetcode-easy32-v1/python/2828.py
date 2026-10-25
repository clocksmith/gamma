"""2828. Check if a String Is an Acronym of Words (Easy).

Specification: https://leetcode.com/problems/check-if-a-string-is-an-acronym-of-words/description/
"""


def solve(words: list[str], s: str) -> bool:
    """O(len(words)) time, O(1) space; compare initials without building a copy."""
    if len(words) != len(s):
        return False
    for index, word in enumerate(words):
        if word[0] != s[index]:
            return False
    return True


class Solution:
    def isAcronym(self, words: list[str], s: str) -> bool:
        return solve(words, s)
