def letter_counts(text: str) -> list[int]:
    counts = [0] * 26
    for character in text:
        counts[ord(character) - ord("a")] += 1
    return counts


class Solution:
    def countCharacters(self, words: list[str], chars: str) -> int:
        available = letter_counts(chars)
        total = 0
        for word in words:
            required = letter_counts(word)
            if all(required[index] <= available[index] for index in range(26)):
                total += len(word)
        return total
