"""1255. Maximum Score Words Formed by Letters (Hard).

Specification: https://leetcode.com/problems/maximum-score-words-formed-by-letters/description/
"""


def solve(words: list[str], letters: list[str], score: list[int]) -> int:
    available = [0] * 26
    for ch in letters:
        available[ord(ch) - 97] += 1
    best = 0

    def backtrack(index, current_score):
        nonlocal best
        best = max(best, current_score)
        for i in range(index, len(words)):
            needed = [0] * 26
            word_score = 0
            for ch in words[i]:
                code = ord(ch) - 97
                needed[code] += 1
                word_score += score[code]
            if any(needed[letter] > available[letter] for letter in range(26)):
                continue
            for letter in range(26):
                available[letter] -= needed[letter]
            backtrack(i + 1, current_score + word_score)
            for letter in range(26):
                available[letter] += needed[letter]

    backtrack(0, 0)
    return best


class Solution:
    def maxScoreWords(self, words: list[str], letters: list[str], score: list[int]) -> int:
        return solve(words, letters, score)
