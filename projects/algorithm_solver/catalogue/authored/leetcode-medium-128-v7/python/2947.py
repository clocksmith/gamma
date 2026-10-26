"""2947. Count Beautiful Substrings I: enumerate substrings while accumulating vowel and consonant counts."""


def solve(s: str, k: int) -> int:
    """O(n * n) time and O(1) auxiliary space; inputs are read-only."""
    vowels = set('aeiou')
    total = 0
    for left in range(len(s)):
        vowel_count = consonant_count = 0
        for right in range(left, len(s)):
            if s[right] in vowels:
                vowel_count += 1
            else:
                consonant_count += 1
            if vowel_count == consonant_count and vowel_count * consonant_count % k == 0:
                total += 1
    return total


class Solution:
    def beautifulSubstrings(self, s: str, k: int) -> int:
        return solve(s, k)
