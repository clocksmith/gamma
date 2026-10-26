"""3042. Count Prefix and Suffix Pairs I (Easy).

Specification: https://leetcode.com/problems/count-prefix-and-suffix-pairs-i/description/
"""


def solve(words: list[str]) -> int:
    """O(n^2 * m) time, O(1) auxiliary space; m is maximum word length; preserve words."""
    pairs = 0
    for left in range(len(words)):
        for right in range(left + 1, len(words)):
            if words[right].startswith(words[left]) and words[right].endswith(words[left]):
                pairs += 1
    return pairs


class Solution:
    def countPrefixSuffixPairs(self, words: list[str]) -> int:
        return solve(words)
