"""127. Word Ladder (Hard).

Specification: https://leetcode.com/problems/word-ladder/description/
"""


def solve(beginWord: str, endWord: str, wordList: list[str]) -> int:
    words = set(wordList)
    if endWord not in words:
        return 0
    queue = [beginWord]
    steps = 1
    visited = {beginWord}
    while queue:
        next_queue = []
        for word in queue:
            if word == endWord:
                return steps
            for i in range(len(word)):
                for code in range(97, 123):
                    candidate = word[:i] + chr(code) + word[i + 1:]
                    if candidate in words and candidate not in visited:
                        visited.add(candidate)
                        next_queue.append(candidate)
        queue = next_queue
        steps += 1
    return 0


class Solution:
    def ladderLength(self, beginWord: str, endWord: str, wordList: list[str]) -> int:
        return solve(beginWord, endWord, wordList)
