"""2451. Odd String Difference (Easy).

Specification: https://leetcode.com/problems/odd-string-difference/description/
"""


def solve(words: list[str]) -> str:
    """O(n * m) expected time and space; group by adjacent-letter differences; preserve words."""
    groups = {}
    for word in words:
        signature = tuple(ord(word[index]) - ord(word[index - 1]) for index in range(1, len(word)))
        if signature not in groups:
            groups[signature] = [word, 0]
        groups[signature][1] += 1
    for word, count in groups.values():
        if count == 1:
            return word
    return ''


class Solution:
    def oddString(self, words: list[str]) -> str:
        return solve(words)
