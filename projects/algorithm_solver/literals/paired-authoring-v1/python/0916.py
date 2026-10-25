def letter_counts(word: str) -> list[int]:
    counts = [0] * 26
    for character in word:
        counts[ord(character) - 97] += 1
    return counts


class Solution:
    def wordSubsets(self, words1: list[str], words2: list[str]) -> list[str]:
        required = [0] * 26
        for word in words2:
            counts = letter_counts(word)
            for index in range(26):
                required[index] = max(required[index], counts[index])

        result = []
        for word in words1:
            counts = letter_counts(word)
            qualifies = True
            for index in range(26):
                if counts[index] < required[index]:
                    qualifies = False
                    break
            if qualifies:
                result.append(word)
        return result
