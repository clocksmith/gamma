"""1456. Maximum Number of Vowels in a Substring of Given Length: update the vowel count as a fixed-length window moves."""


def solve(s: str, k: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    vowels = frozenset('aeiou')
    count = best = 0
    for index, letter in enumerate(s):
        count += letter in vowels
        if index >= k:
            count -= s[index - k] in vowels
        if index + 1 >= k:
            best = max(best, count)
    return best


class Solution:
    def maxVowels(self, s: str, k: int) -> int:
        return solve(s, k)
