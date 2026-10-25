class Solution:
    def longestStrChain(self, words):
        ordered = sorted(words, key=len)
        ending = {}
        best = 0
        for word in ordered:
            length = 1
            for index in range(len(word)):
                predecessor = word[:index] + word[index + 1:]
                length = max(length, ending.get(predecessor, 0) + 1)
            ending[word] = max(ending.get(word, 0), length)
            best = max(best, ending[word])
        return best
