def letter_counts(text: str) -> list[int]:
    counts = [0] * 26
    for character in text:
        counts[ord(character) - ord("a")] += 1
    return counts


def upper_bound(values: list[int], target: int) -> int:
    left = 0
    right = len(values)
    while left < right:
        middle = left + (right - left) // 2
        if values[middle] <= target:
            left = middle + 1
        else:
            right = middle
    return left


class Solution:
    def numSmallerByFrequency(self, queries: list[str], words: list[str]) -> list[int]:
        frequencies = []
        for word in words:
            counts = letter_counts(word)
            frequencies.append(next(count for count in counts if count > 0))
        frequencies.sort()
        output = []
        for query in queries:
            counts = letter_counts(query)
            frequency = next(count for count in counts if count > 0)
            first_greater = upper_bound(frequencies, frequency)
            output.append(len(frequencies) - first_greater)
        return output
