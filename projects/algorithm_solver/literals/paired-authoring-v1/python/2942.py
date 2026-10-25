class Solution:
    def findWordsContaining(self, words: list[str], x: str) -> list[int]:
        output = []
        for index, word in enumerate(words):
            for character in word:
                if character == x:
                    output.append(index)
                    break
        return output
