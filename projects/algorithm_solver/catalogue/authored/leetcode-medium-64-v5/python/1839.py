"""1839. Longest Substring Of All Vowels in Order: track nondecreasing vowel runs containing all five distinct vowels."""


def solve(word: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    best = run = distinct = 0
    previous = ''
    for vowel in word:
        if not previous or vowel < previous:
            run = distinct = 1
        else:
            run += 1
            if vowel > previous:
                distinct += 1
        if distinct == 5:
            best = max(best, run)
        previous = vowel
    return best


class Solution:
    def longestBeautifulSubstring(self, word: str) -> int:
        return solve(word)
