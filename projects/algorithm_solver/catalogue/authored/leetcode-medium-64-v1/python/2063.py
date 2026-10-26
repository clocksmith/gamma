"""2063. Vowels of All Substrings: count how many substrings include each vowel position."""


def solve(word: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    answer = 0
    size = len(word)
    for index, character in enumerate(word):
        if character in 'aeiou':
            answer += (index + 1) * (size - index)
    return answer


class Solution:
    def countVowels(self, word: str) -> int:
        return solve(word)
