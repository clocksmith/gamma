"""126. Word Ladder II."""
from collections import defaultdict, deque

def solve(beginWord: str, endWord: str, wordList: list[str]) -> list[list[str]]:
    words = set(wordList)
    if endWord not in words:
        return []
    parents = defaultdict(list)
    distance = {beginWord: 0}
    queue = deque([beginWord])
    length = len(beginWord)
    while queue:
        word = queue.popleft()
        step = distance[word] + 1
        for index in range(length):
            prefix, suffix = word[:index], word[index + 1:]
            for code in range(97, 123):
                candidate = prefix + chr(code) + suffix
                if candidate not in words:
                    continue
                if candidate not in distance:
                    distance[candidate] = step
                    queue.append(candidate)
                if distance[candidate] == step:
                    parents[candidate].append(word)
        if endWord in distance and step >= distance[endWord]:
            continue
    if endWord not in distance:
        return []
    result = []
    path = [endWord]
    def build(word: str) -> None:
        if word == beginWord:
            result.append(path[::-1])
            return
        for parent in parents[word]:
            path.append(parent)
            build(parent)
            path.pop()
    build(endWord)
    return result

class Solution:
    def findLadders(self, beginWord, endWord, wordList):
        return solve(beginWord, endWord, wordList)
