class Solution:
    def toGoatLatin(self, sentence: str) -> str:
        words = sentence.split(" ")
        result = []
        for index, word in enumerate(words, 1):
            if word[0] not in "aeiouAEIOU":
                word = word[1:] + word[0]
            result.append(word + "ma" + "a" * index)
        return " ".join(result)
