class Solution:
    def ladderLength(self, beginWord: str, endWord: str, wordList: list[str]) -> int:
        remaining = set(wordList)
        if endWord not in remaining:
            return 0
        remaining.discard(beginWord)
        queue = [(beginWord, 1)]
        head = 0
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        while head < len(queue):
            word, distance = queue[head]
            head += 1
            if word == endWord:
                return distance
            for position in range(len(word)):
                for letter in alphabet:
                    if letter == word[position]:
                        continue
                    candidate = word[:position] + letter + word[position + 1:]
                    if candidate in remaining:
                        remaining.remove(candidate)
                        queue.append((candidate, distance + 1))
        return 0
