"""2744. Find Maximum Number of String Pairs (Easy).

Specification: https://leetcode.com/problems/find-maximum-number-of-string-pairs/description/
"""


def solve(words: list[str]) -> int:
    """O(n) expected time, O(n) space; inputs contain distinct two-letter words."""
    unmatched = set()
    pairs = 0
    for word in words:
        reversed_word = word[1] + word[0]
        if reversed_word in unmatched:
            unmatched.remove(reversed_word)
            pairs += 1
        else:
            unmatched.add(word)
    return pairs


class Solution:
    def maximumNumberOfStringPairs(self, words: list[str]) -> int:
        return solve(words)
