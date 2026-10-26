"""2255. Count Prefixes of a Given String (Easy).

Specification: https://leetcode.com/problems/count-prefixes-of-a-given-string/description/
"""


def solve(words: list[str], s: str) -> int:
    """O(total word characters) time, O(1) auxiliary space; preserve words."""
    result = 0
    for word in words:
        if s.startswith(word):
            result += 1
    return result


class Solution:
    def countPrefixes(self, words: list[str], s: str) -> int:
        return solve(words, s)
