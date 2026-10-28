"""Original frontend 126 source-defined native ABI; qualification unknown."""

def solve(beginWord, endWord, wordList):
    from collections import deque
    words = set(wordList)
    if endWord not in words:
        return []
    distance = {beginWord: 0}
    parents = {}
    queue = deque([beginWord])
    shortest = float('inf')
    while queue:
        current = queue.popleft()
        depth = distance[current]
        if depth >= shortest:
            continue
        for i in range(len(current)):
            for char in 'abcdefghijklmnopqrstuvwxyz':
                if char == current[i]:
                    continue
                following = current[:i] + char + current[i + 1:]
                if following not in words:
                    continue
                if following not in distance:
                    distance[following] = depth + 1
                    parents[following] = []
                    queue.append(following)
                if distance[following] == depth + 1:
                    parents[following].append(current)
                    if following == endWord:
                        shortest = depth + 1
    if endWord not in distance:
        return []
    answer = []
    pending = [(endWord, [endWord])]
    while pending:
        word, reverse_path = pending.pop()
        if word == beginWord:
            answer.append(reverse_path[::-1])
        else:
            pending.extend((parent, reverse_path + [parent]) for parent in parents[word])
    return answer


class Solution:
    def findLadders(self, beginWord, endWord, wordList):
        return solve(beginWord, endWord, wordList)
