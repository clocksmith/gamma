"""1170. Compare Strings by Frequency of the Smallest Character (Easy).

Specification: https://leetcode.com/problems/compare-strings-by-frequency-of-the-smallest-character/description/
"""


def solve(queries: list[str], words: list[str]) -> list[int]:
    """O(L + w log w + q log w) time, O(w + q) space; upper-bound search counts strictly greater frequencies."""
    def frequency(text):
        smallest = '{'
        count = 0
        for character in text:
            if character < smallest:
                smallest = character
                count = 1
            elif character == smallest:
                count += 1
        return count

    frequencies = sorted(frequency(word) for word in words)
    result = []
    for query in queries:
        target = frequency(query)
        left, right = 0, len(frequencies)
        while left < right:
            middle = left + (right - left) // 2
            if frequencies[middle] <= target:
                left = middle + 1
            else:
                right = middle
        result.append(len(frequencies) - left)
    return result


class Solution:
    def numSmallerByFrequency(self, queries: list[str], words: list[str]) -> list[int]:
        return solve(queries, words)
