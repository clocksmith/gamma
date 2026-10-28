"""1178. Number of Valid Words for Each Puzzle (Medium).

Specification: https://leetcode.com/problems/number-of-valid-words-for-each-puzzle/description/
"""


def _mask(w: str) -> int:
    m = 0
    for ch in w:
        m |= 1 << (ord(ch) - 97)
    return m


def solve(words: list[str], puzzles: list[str]) -> list[int]:
    freq = {}
    for w in words:
        m = _mask(w)
        freq[m] = freq.get(m, 0) + 1
    out = []
    for p in puzzles:
        pm = _mask(p)
        first = 1 << (ord(p[0]) - 97)
        count = 0
        sub = pm
        while sub > 0:
            if sub & first:
                count += freq.get(sub, 0)
            sub = (sub - 1) & pm
        out.append(count)
    return out


class Solution:
    def findNumOfValidWords(self, words: list[str], puzzles: list[str]) -> list[int]:
        return solve(words, puzzles)
