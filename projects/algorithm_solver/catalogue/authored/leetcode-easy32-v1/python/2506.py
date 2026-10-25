"""2506. Count Pairs Of Similar Strings (Easy).

Specification: https://leetcode.com/problems/count-pairs-of-similar-strings/description/
"""


def solve(words: list[str]) -> int:
    """O(total characters) expected time, O(u) space for distinct masks."""
    counts = {}
    result = 0
    for word in words:
        mask = 0
        for character in word:
            mask |= 1 << (ord(character) - ord('a'))
        previous = counts.get(mask, 0)
        result += previous
        counts[mask] = previous + 1
    return result


class Solution:
    def similarPairs(self, words: list[str]) -> int:
        return solve(words)
