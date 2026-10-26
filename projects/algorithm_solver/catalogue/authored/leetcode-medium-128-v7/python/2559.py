"""2559. Count Vowel Strings in Ranges: answer range counts from prefix totals of words with vowel endpoints."""


def solve(words: list[str], queries: list[list[int]]) -> list[int]:
    """O(n + q) time and O(n + q) auxiliary space; inputs are read-only."""
    vowels = set('aeiou')
    prefix = [0]
    for word in words:
        prefix.append(prefix[-1] + int(word[0] in vowels and word[-1] in vowels))
    return [prefix[right + 1] - prefix[left] for left, right in queries]


class Solution:
    def vowelStrings(self, words: list[str], queries: list[list[int]]) -> list[int]:
        return solve(words, queries)
