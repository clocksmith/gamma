"""2185. Counting Words With a Given Prefix (Easy).

Specification: https://leetcode.com/problems/counting-words-with-a-given-prefix/description/
"""


def solve(words: list[str], pref: str) -> int:
    """O(n * p) time for n words and prefix length p, O(1) auxiliary space; preserve words."""
    return sum(word.startswith(pref) for word in words)


class Solution:
    def prefixCount(self, words: list[str], pref: str) -> int:
        return solve(words, pref)
