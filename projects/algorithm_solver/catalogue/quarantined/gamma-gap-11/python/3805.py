"""3805. Count Caesar Cipher Pairs."""
from __future__ import annotations


def solve(words: list[str]) -> int:
    """O(S) expected time and O(S) space for S total ASCII characters; inputs are preserved."""
    frequencies = {}
    answer = 0
    for word in words:
        first = ord(word[0])
        key = bytes((ord(char) - first) % 26 for char in word)
        previous = frequencies.get(key, 0)
        answer += previous
        frequencies[key] = previous + 1
    return answer


class Solution:
    def countPairs(self, words: list[str]) -> int:
        return solve(words)
