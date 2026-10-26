"""1657. Determine if Two Strings Are Close: require the same letter support and the same multiset of frequencies."""


def solve(word1: str, word2: str) -> bool:
    """O(n + m) time and O(1) auxiliary space for the fixed lowercase alphabet; inputs are read-only."""
    if len(word1) != len(word2):
        return False
    first = [0] * 26
    second = [0] * 26
    for letter in word1:
        first[ord(letter) - ord('a')] += 1
    for letter in word2:
        second[ord(letter) - ord('a')] += 1
    if any((left == 0) != (right == 0) for left, right in zip(first, second)):
        return False
    return sorted(first) == sorted(second)


class Solution:
    def closeStrings(self, word1: str, word2: str) -> bool:
        return solve(word1, word2)
