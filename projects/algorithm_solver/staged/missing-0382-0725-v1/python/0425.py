"""425. Word Squares. Backtrack only through words having the required column prefix."""

from collections import defaultdict

def solve(words: list[str]) -> list[list[str]]:
    if not words:
        return []
    size = len(words[0])
    prefixes = defaultdict(list)
    for word in words:
        for end in range(size + 1):
            prefixes[word[:end]].append(word)
    answer, square = [], []
    def extend():
        row = len(square)
        if row == size:
            answer.append(square[:])
            return
        prefix = ''.join(word[row] for word in square)
        for word in prefixes.get(prefix, ()):
            square.append(word)
            extend()
            square.pop()
    extend()
    return answer


class Solution:
    def wordSquares(self, words: list[str]) -> list[list[str]]:
        return solve(words)
