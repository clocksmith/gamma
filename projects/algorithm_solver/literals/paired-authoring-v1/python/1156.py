def letter_counts(text: str) -> list[int]:
    counts = [0] * 26
    for character in text:
        counts[ord(character) - ord("a")] += 1
    return counts


class Solution:
    def maxRepOpt1(self, text: str) -> int:
        totals = letter_counts(text)
        best = 0
        for letter_index in range(26):
            if totals[letter_index] == 0:
                continue
            letter = chr(ord("a") + letter_index)
            left = 0
            different = 0
            for right, character in enumerate(text):
                if character != letter:
                    different += 1
                while different > 1:
                    if text[left] != letter:
                        different -= 1
                    left += 1
                best = max(best, min(right - left + 1, totals[letter_index]))
        return best
