def letter_counts(text: str) -> list[int]:
    counts = [0] * 26
    for character in text:
        counts[ord(character) - ord("a")] += 1
    return counts


class Solution:
    def rearrangeCharacters(self, s: str, target: str) -> int:
        available = letter_counts(s)
        required = letter_counts(target)
        copies = len(s)
        for index in range(26):
            if required[index] > 0:
                copies = min(copies, available[index] // required[index])
        return copies
