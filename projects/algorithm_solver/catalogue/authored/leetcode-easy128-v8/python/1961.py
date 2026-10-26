"""1961. Check If String Is a Prefix of Array (Easy).

Specification: https://leetcode.com/problems/check-if-string-is-a-prefix-of-array/description/
"""


def solve(s: str, words: list[str]) -> bool:
    """O(total compared characters) time, O(1) auxiliary space; accept only at whole-word boundaries."""
    matched = 0
    for word in words:
        if not s.startswith(word, matched):
            return False
        matched += len(word)
        if matched == len(s):
            return True
    return False


class Solution:
    def isPrefixString(self, s: str, words: list[str]) -> bool:
        return solve(s, words)
