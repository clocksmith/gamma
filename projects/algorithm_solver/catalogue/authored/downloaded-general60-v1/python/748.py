"""748. Shortest Completing Word (Easy).

Specification: https://leetcode.com/problems/shortest-completing-word/description/
"""


def _counts_of(text):
    counts = {}
    for ch in text.lower():
        if 'a' <= ch <= 'z':
            counts[ch] = counts.get(ch, 0) + 1
    return counts


def solve(licensePlate: str, words: list[str]) -> str:
    need = _counts_of(licensePlate)
    best = None
    for word in words:
        have = _counts_of(word)
        if all(have.get(ch, 0) >= count for ch, count in need.items()):
            if best is None or len(word) < len(best):
                best = word
    return best


class Solution:
    def shortestCompletingWord(self, licensePlate: str, words: list[str]) -> str:
        return solve(licensePlate, words)
